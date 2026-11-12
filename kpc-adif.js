/* KPC ADIF Log Checker & Editor (kpc-adif.html, members only).
   Brandon Oct 31 4:05 PM: 'a log checker for pota and qrz and then an adif editor like adif master, all just buttons'.
   Brandon Oct 31 4:25 PM: 'make it work for anyones logs … options to set it up for pota style saves … all the options adif
   master has … a map and qso rate per 15 qso fastest, 30 min average speed, etc … lots of details, make it nice'.
   Uses KPCAdif (kpc-adif-lib.js). The log stays in this browser. The N4KPC uploader hands a file over in sessionStorage
   'kpcAdifHand' and gets the fixed log back in 'kpcAdifBack'. Settings: localStorage 'kpcAdifSet'. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id), A = window.KPCAdif;
  if (!$('ae') || !A) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = x => (x || 0).toLocaleString();
  const FIRST = ['CALL', 'QSO_DATE', 'TIME_ON', 'BAND', 'FREQ', 'MODE', 'SUBMODE', 'RST_SENT', 'RST_RCVD', 'NAME', 'STATE', 'GRIDSQUARE', 'SIG', 'SIG_INFO', 'STATION_CALLSIGN', 'OPERATOR', 'MY_SIG', 'MY_SIG_INFO', 'MY_GRIDSQUARE', 'COMMENT'];
  const PAGE = 200;
  let header = '', recs = [], name = '', issues = [], undo = [], redo = [], extra = [], hidden = new Set(), order = null, sortBy = null, sortDir = 1, filt = '', page = 0, tab = 'edit', map = null, mapL = null;
  /* ---- settings (kept on this device) ---- */
  const DEF = { mycall: '', qrzOn: true, qrz: '', potaOn: true, potaSplit: 'park', potaName: '{CALL}@{PARK}-{DATE}', potaAddSig: true, p2p: true };
  let S = DEF; try { S = Object.assign({}, DEF, JSON.parse(localStorage.getItem('kpcAdifSet') || '{}')); } catch (e) {}
  const saveS = () => { try { localStorage.setItem('kpcAdifSet', JSON.stringify(S)); } catch (e) {} };
  const opt = () => ({ qrz: S.qrzOn ? (String(S.qrz || S.mycall || '').toUpperCase().trim()) : '', pota: !!S.potaOn });
  const say = (t, bad) => { const m = $('aeMsg'); m.textContent = t || ''; m.style.color = bad ? '#d0452e' : ''; };
  const snap = () => { undo.push(JSON.stringify(recs)); if (undo.length > 40) undo.shift(); redo = []; $('aeUndo').disabled = false; $('aeRedo').disabled = true; };

  /* ---------- columns + the shown rows ---------- */
  function allCols() {
    const have = new Set(); recs.forEach(r => Object.keys(r).forEach(k => have.add(k))); extra.forEach(k => have.add(k));
    ['CALL', 'QSO_DATE', 'TIME_ON', 'BAND', 'MODE'].forEach(k => have.add(k));
    const base = FIRST.filter(k => have.has(k)).concat([...have].filter(k => !FIRST.includes(k)).sort());
    if (order) { const o = order.filter(k => have.has(k)); return o.concat(base.filter(k => !o.includes(k))); }
    return base;
  }
  const cols = () => allCols().filter(c => !hidden.has(c));
  function shown() {
    let ix = recs.map((r, i) => i);
    if (filt) { const q = filt.toUpperCase(); ix = ix.filter(i => Object.values(recs[i]).some(v => String(v).toUpperCase().includes(q))); }
    if (sortBy) { const k = sortBy, numeric = /^(FREQ|TX_PWR|RX_PWR|SRX|STX|DXCC|AGE|ANT_AZ)$/.test(k); ix.sort((a, b) => { const x = recs[a][k] || '', y = recs[b][k] || ''; return (numeric ? (+x || 0) - (+y || 0) : String(x).localeCompare(String(y))) * sortDir || a - b; }); }
    return ix;
  }

  /* ---------- check ---------- */
  function run() {
    issues = A.check(recs, opt());
    const e = issues.filter(x => x.level === 'error').length, w = issues.length - e, o = opt();
    const forTxt = [o.qrz ? 'QRZ (' + o.qrz + ')' : '', o.pota ? 'POTA' : ''].filter(Boolean).join(' and ') || 'ADIF basics';
    $('aeSum').innerHTML = recs.length ? '<span class="pill">' + num(recs.length) + ' contact' + (recs.length > 1 ? 's' : '') + '</span>' +
      (issues.length ? (e ? '<button type="button" class="pill err" data-tab="check">✕ ' + e + ' problem' + (e > 1 ? 's' : '') + '</button>' : '') + (w ? '<button type="button" class="pill wrn" data-tab="check">⚠ ' + w + ' to look at</button>' : '') : '<span class="pill ok">✓ Looks good for ' + esc(forTxt) + '</span>') : '';
    const L = $('aeIss');
    L.innerHTML = issues.length ? issues.slice(0, 500).map((x, k) => '<li><b class="' + (x.level === 'error' ? 'e' : 'w') + '">' + (x.level === 'error' ? '✕' : '⚠') + ' ' + (x.i >= 0 ? 'Contact ' + (x.i + 1) + (recs[x.i] && recs[x.i].CALL ? ' · ' + esc(recs[x.i].CALL) : '') : 'Whole file') + '</b><span>' + esc(x.msg) + '</span>' +
      (x.fix ? '<button type="button" data-fix="' + k + '">' + (x.fix.kind === 'delete' ? 'DELETE IT' : x.fix.kind === 'split' ? 'SAVE FOR POTA' : 'FIX') + '</button>' : '') + (x.i >= 0 ? '<button type="button" data-go="' + x.i + '">SHOW</button>' : '') + '</li>').join('') + (issues.length > 500 ? '<li>…and ' + (issues.length - 500) + ' more.</li>' : '')
      : '<li><b class="ok">✓</b><span>' + (recs.length ? 'Nothing to fix for ' + esc(forTxt) + '.' : 'Open a log first.') + '</span></li>';
    $('aeCheckFor').textContent = 'Checking for ' + forTxt + '. Change it in ⚙ SET UP.';
    grid();
    if (tab === 'stats') stats(); if (tab === 'map') drawMap();
  }

  /* ---------- grid ---------- */
  function grid() {
    const C = cols(), bad = {}, ix = shown(), pages = Math.max(1, Math.ceil(ix.length / PAGE));
    if (page >= pages) page = pages - 1;
    issues.forEach(x => { if (x.i >= 0) bad[x.i + '|' + x.field] = x.level === 'error' ? 'bad' : 'wrn'; });
    const show = ix.slice(page * PAGE, page * PAGE + PAGE);
    $('aeEmpty').hidden = !!recs.length; ['aeWork', 'aeTabs'].forEach(id => { $(id).hidden = !recs.length; });
    $('aeGrid').innerHTML = '<thead><tr><th><input type="checkbox" id="aeAll" aria-label="Tick every contact shown"></th><th>#</th>' + C.map(c => '<th><button type="button" class="srt" data-sort="' + esc(c) + '" title="' + esc(A.FIELDS[c] || c) + '">' + esc(c) + (sortBy === c ? (sortDir > 0 ? ' ▲' : ' ▼') : '') + '</button></th>').join('') + '</tr></thead><tbody>' +
      show.map(i => { const r = recs[i]; return '<tr data-r="' + i + '"><td><input type="checkbox" data-tick="' + i + '"' + (TICK.has(i) ? ' checked' : '') + ' aria-label="Tick contact ' + (i + 1) + '"></td><td class="n">' + (i + 1) + '</td>' +
        C.map(c => '<td class="' + (bad[i + '|' + c] || '') + '"><input type="text" data-c="' + esc(c) + '" value="' + esc(r[c] || '') + '" aria-label="' + esc(c) + ' of contact ' + (i + 1) + '"></td>').join('') + '</tr>'; }).join('') + '</tbody>';
    $('aeCount').textContent = (filt ? num(ix.length) + ' of ' + num(recs.length) + ' contacts match' : num(recs.length) + ' contacts') + (TICK.size ? ' · ' + num(TICK.size) + ' ticked' : '') + (hidden.size ? ' · ' + hidden.size + ' column' + (hidden.size > 1 ? 's' : '') + ' hidden' : '');
    $('aePg').hidden = pages < 2; $('aePgT').textContent = 'Page ' + (page + 1) + ' of ' + pages; $('aePrev').disabled = page === 0; $('aeNext').disabled = page >= pages - 1;
    $('aeDel').disabled = $('aeCopy').disabled = !TICK.size;
    fieldLists();
  }
  const TICK = new Set();
  function fieldLists() {
    const have = allCols(), cat = Object.keys(A.FIELDS).filter(k => !have.includes(k)).sort();
    const o = k => '<option value="' + esc(k) + '">' + esc(k) + (A.FIELDS[k] ? ' · ' + esc(A.FIELDS[k]) : '') + '</option>';
    $('aeBF').innerHTML = '<optgroup label="In this log">' + have.map(o).join('') + '</optgroup><optgroup label="Other ADIF fields">' + cat.map(o).join('') + '</optgroup>';
    $('aeBFrom').innerHTML = have.map(o).join('');
    $('aeFindF').innerHTML = '<option value="*">Every field</option>' + have.map(o).join('');
    $('aeColList').innerHTML = allCols().map((c, k) => '<li><label><input type="checkbox" data-show="' + esc(c) + '"' + (hidden.has(c) ? '' : ' checked') + '> <b>' + esc(c) + '</b> <small>' + esc(A.FIELDS[c] || '') + '</small></label><span><button type="button" data-up="' + esc(c) + '" aria-label="Move ' + esc(c) + ' left"' + (k ? '' : ' disabled') + '>▲</button><button type="button" data-ren="' + esc(c) + '">RENAME</button><button type="button" data-drop="' + esc(c) + '">DELETE FIELD</button></span></li>').join('');
    $('aeNewCol').innerHTML = cat.map(o).join('');
  }

  /* ---------- open / save ---------- */
  function load(text, nm, add) {
    const p = A.parse(text);
    if (add && recs.length) { snap(); recs = recs.concat(p.recs); name = name.replace(/\.(adi|adif)$/i, '') + '+' + nm; say(num(p.recs.length) + ' contacts added from ' + nm + '. Use DUPLICATES to find any doubles.'); }
    else { header = p.header; recs = p.recs; name = nm || 'log.adi'; undo = []; redo = []; extra = []; hidden = new Set(); order = null; sortBy = null; TICK.clear(); page = 0; filt = ''; $('aeFilt').value = ''; $('aeUndo').disabled = $('aeRedo').disabled = true; say(''); }
    $('aeName').textContent = recs.length ? 'Open: ' + name : 'No contacts found in ' + nm + '. Is it an ADIF (.adi) or CSV file?';
    if (!S.mycall) { const sc = recs.map(r => r.STATION_CALLSIGN || r.OPERATOR).filter(Boolean); if (sc.length) { const c = {}; sc.forEach(x => { c[x] = (c[x] || 0) + 1; }); $('aeMy').placeholder = 'From the log: ' + Object.keys(c).sort((a, b) => c[b] - c[a])[0]; } }
    run(); if (recs.length) setTab(tab === 'check' || issues.some(x => x.level === 'error') ? 'check' : tab);
  }
  /* CSV in: first row = field names */
  function csvParse(text) {
    const rows = []; let row = [], cur = '', q = false;
    for (let i = 0; i < text.length; i++) { const ch = text[i];
      if (q) { if (ch === '"' && text[i + 1] === '"') { cur += '"'; i++; } else if (ch === '"') q = false; else cur += ch; }
      else if (ch === '"') q = true; else if (ch === ',') { row.push(cur); cur = ''; } else if (ch === '\n' || ch === '\r') { if (ch === '\r' && text[i + 1] === '\n') i++; row.push(cur); rows.push(row); row = []; cur = ''; } else cur += ch; }
    if (cur || row.length) { row.push(cur); rows.push(row); }
    const H = (rows.shift() || []).map(h => h.trim().toUpperCase().replace(/[^A-Z0-9_]/g, '_'));
    return rows.filter(r => r.some(x => x.trim())).map(r => { const o = {}; H.forEach((h, k) => { if (h && r[k] != null && String(r[k]).trim() !== '') o[h] = String(r[k]).trim(); }); return o; });
  }
  function csvOut(list) { const C = allCols(), q = v => /[",\n]/.test(v) ? '"' + String(v).replace(/"/g, '""') + '"' : String(v); return C.join(',') + '\n' + list.map(r => C.map(c => q(r[c] == null ? '' : r[c])).join(',')).join('\n') + '\n'; }
  function download(text, fn, type) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: type || 'text/plain' })); a.download = fn; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500); }
  const base = () => name.replace(/\.(adi|adif|csv)$/i, '') || 'log';
  /* POTA-style save (docs.pota.app 'Submitting logs': CALL@PARK-YYYYMMDD.adi; one park + one activating call per upload) */
  function potaSave() {
    const my = String(S.mycall || '').toUpperCase().trim(), g = {};
    const list = recs.map(r => { const o = Object.assign({}, r);
      if (S.potaAddSig && (o.MY_SIG_INFO || o.MY_POTA_REF) && !o.MY_SIG) o.MY_SIG = 'POTA';
      if (S.potaAddSig && !o.MY_SIG_INFO && o.MY_POTA_REF) o.MY_SIG_INFO = o.MY_POTA_REF;
      if (S.p2p && (o.POTA_REF || o.SIG_INFO) && !o.SIG) { o.SIG = 'POTA'; if (!o.SIG_INFO) o.SIG_INFO = o.POTA_REF; }
      if (!o.STATION_CALLSIGN && my) o.STATION_CALLSIGN = my; return o; });
    list.forEach(r => { const park = String(r.MY_SIG_INFO || '').toUpperCase().split(/[,\s]+/)[0] || 'NO-PARK', st = String(r.STATION_CALLSIGN || r.OPERATOR || my || 'CALL').toUpperCase(), d = String(r.QSO_DATE || '');
      const k = S.potaSplit === 'one' ? 'ALL' : S.potaSplit === 'day' ? park + '|' + st + '|' + d : park + '|' + st; (g[k] = g[k] || []).push(r); });
    const files = Object.entries(g).map(([k, L]) => { const r0 = L[0], park = String(r0.MY_SIG_INFO || '').toUpperCase().split(/[,\s]+/)[0] || 'NO-PARK', call = String(r0.STATION_CALLSIGN || r0.OPERATOR || my || 'CALL').toUpperCase().replace(/\//g, '-'), d = String(L.map(r => r.QSO_DATE || '').sort()[0] || '');
      const fn = (S.potaSplit === 'one' ? base() + '-pota' : String(S.potaName || DEF.potaName).replace('{CALL}', call).replace('{PARK}', park).replace('{DATE}', d).replace('{STATE}', r0.MY_STATE || '')).replace(/[^A-Za-z0-9@._+-]/g, '_') + '.adi'; return { fn, L }; });
    files.forEach((f, j) => setTimeout(() => download(A.write(header, f.L), f.fn), j * 450));
    say(files.length + ' POTA file' + (files.length > 1 ? 's' : '') + ' saved: ' + files.map(f => f.fn + ' (' + f.L.length + ')').join(', ') + '. Upload each on POTA → My Log Uploads.' + (files.some(f => /NO-PARK/.test(f.fn)) ? ' One has no park (MY_SIG_INFO): set it before you upload.' : ''));
  }

  /* ---------- bulk edit ---------- */
  function targets() { const w = $('aeBT').value; return w === 'tick' ? [...TICK] : w === 'shown' ? shown() : recs.map((r, i) => i); }
  function shiftTime(r, mins) { const t = A.when(r); if (t == null) return false;
    if (r.TIME_OFF) { const o = A.when({ QSO_DATE: r.QSO_DATE_OFF || r.QSO_DATE, TIME_ON: r.TIME_OFF }); if (o != null) { const d2 = new Date(o + mins * 6e4); r.TIME_OFF = d2.toISOString().slice(11, 19).replace(/:/g, '').slice(0, String(r.TIME_OFF).length > 4 ? 6 : 4); if (r.QSO_DATE_OFF) r.QSO_DATE_OFF = d2.toISOString().slice(0, 10).replace(/-/g, ''); } }
    const d = new Date(t + mins * 6e4); r.QSO_DATE = d.toISOString().slice(0, 10).replace(/-/g, ''); r.TIME_ON = d.toISOString().slice(11, 19).replace(/:/g, '').slice(0, String(r.TIME_ON).length > 4 ? 6 : 4); return true; }
  function bulk() {
    const T = targets(), f = $('aeBF').value, act = $('aeBA').value, v = $('aeBV').value.trim(); if (!T.length) return say('Nothing to change: tick some contacts or pick "every contact".', true);
    snap(); let n = 0;
    T.forEach(i => { const r = recs[i]; if (!r) return;
      if (act === 'set') { if (v) { r[f] = v; n++; } }
      else if (act === 'clear') { if (f in r) { delete r[f]; n++; } }
      else if (act === 'upper') { if (r[f] && r[f] !== String(r[f]).toUpperCase()) { r[f] = String(r[f]).toUpperCase(); n++; } }
      else if (act === 'copy') { const from = $('aeBFrom').value; if (r[from] != null && r[from] !== '') { r[f] = r[from]; n++; } }
      else if (act === 'fill') { if (!r[f] && v) { r[f] = v; n++; } }
      else if (act === 'shift') { if (shiftTime(r, +v || 0)) n++; }
      else if (act === 'band') { const b = A.bandOf(r.FREQ); if (b && r.BAND !== b) { r.BAND = b; n++; } } });
    say(n + ' contact' + (n === 1 ? '' : 's') + ' changed.'); run();
  }
  function dupes() { const seen = {}, out = []; recs.forEach((r, i) => { const k = [String(r.CALL || '').toUpperCase(), r.QSO_DATE, String(r.BAND || A.bandOf(r.FREQ)).toLowerCase(), String(r.SUBMODE || r.MODE || '').toUpperCase(), String(r.MY_SIG_INFO || '').toUpperCase()].join('|'); if (k in seen) out.push(i); else seen[k] = i; }); return out; }

  /* ---------- stats ---------- */
  const HH = ms => new Date(ms).toISOString().slice(11, 16);
  const DD = ms => new Date(ms).toISOString().slice(0, 10);
  const dur = m => m >= 120 ? Math.floor(m / 60) + ' h ' + Math.round(m % 60) + ' min' : Math.round(m) + ' min';
  function table(title, rows, total) { const max = Math.max(1, ...rows.map(r => r[1])); return '<div class="st-card"><h3>' + esc(title) + '</h3>' + (rows.length ? '<table class="st-t">' + rows.map(r => '<tr><td>' + esc(r[0]) + '</td><td class="st-b"><i style="width:' + (r[1] / max * 100).toFixed(1) + '%"></i></td><td class="st-n">' + num(r[1]) + (total ? ' <small>' + Math.round(r[1] / total * 100) + '%</small>' : '') + '</td></tr>').join('') + '</table>' : '<p class="info">Nothing in this log.</p>') + '</div>'; }
  const tally = (f) => { const c = {}; recs.forEach(r => { const k = f(r); if (k) c[k] = (c[k] || 0) + 1; }); return Object.entries(c).sort((a, b) => b[1] - a[1]); };
  function stats() {
    const N = recs.length, T = recs.map(A.when).filter(x => x != null).sort((a, b) => a - b), el = $('aeStats');
    if (!N) { el.innerHTML = ''; return; }
    const calls = new Set(recs.map(r => String(r.CALL || '').toUpperCase()).filter(Boolean));
    let tiles = [['Contacts', num(N)], ['Different calls', num(calls.size)], ['Duplicates', num(dupes().length)]];
    let rate = '';
    if (T.length > 1) {
      const span = (T[T.length - 1] - T[0]) / 6e4; let active = 0, gap = 0, gapAt = 0;
      for (let i = 1; i < T.length; i++) { const d = (T[i] - T[i - 1]) / 6e4; if (d <= 30) active += d; if (d > gap) { gap = d; gapAt = T[i - 1]; } }
      const best = n => { if (T.length < n) return null; let b = Infinity, at = 0; for (let i = 0; i + n - 1 < T.length; i++) { const d = T[i + n - 1] - T[i]; if (d < b) { b = d; at = T[i]; } } const m = Math.max(b / 6e4, 0.5); return { m, at, rate: n / m * 60 }; };
      const win = w => { let b = 0, at = 0, j = 0; for (let i = 0; i < T.length; i++) { while (T[i] - T[j] >= w * 6e4) j++; if (i - j + 1 > b) { b = i - j + 1; at = T[j]; } } return { n: b, at, rate: b / w * 60 }; };
      const b10 = best(10), b15 = best(15), b25 = best(25), w15 = win(15), w30 = win(30), w60 = win(60);
      const days = new Set(T.map(DD)).size;
      tiles = tiles.concat([['First contact', DD(T[0]) + ' ' + HH(T[0]) + 'Z'], ['Last contact', DD(T[T.length - 1]) + ' ' + HH(T[T.length - 1]) + 'Z'], ['Days on the air', num(days)], ['On the air', dur(active || span)], ['Average rate', (active ? (N / active * 60).toFixed(1) : '–') + ' / hour'], ['Longest break', dur(gap)]]);
      const rr = (lab, o, txt) => '<tr><td>' + esc(lab) + '</td><td class="st-n"><b>' + (o ? txt(o) : '–') + '</b></td><td>' + (o ? esc(DD(o.at) + ' from ' + HH(o.at) + 'Z') : 'not enough contacts') + '</td></tr>';
      rate = '<div class="st-card wide"><h3>Best rates</h3><table class="st-t r">' +
        rr('Fastest 10 contacts', b10, o => (o.rate).toFixed(0) + ' / hour <small>(' + o.m.toFixed(1) + ' min)</small>') +
        rr('Fastest 15 contacts', b15, o => (o.rate).toFixed(0) + ' / hour <small>(' + o.m.toFixed(1) + ' min)</small>') +
        rr('Fastest 25 contacts', b25, o => (o.rate).toFixed(0) + ' / hour <small>(' + o.m.toFixed(1) + ' min)</small>') +
        rr('Best 15 minutes', w15.n ? w15 : null, o => o.n + ' contacts <small>(' + o.rate.toFixed(0) + ' / hour)</small>') +
        rr('Best 30 minutes', w30.n ? w30 : null, o => o.n + ' contacts <small>(' + o.rate.toFixed(0) + ' / hour)</small>') +
        rr('Best 60 minutes', w60.n ? w60 : null, o => o.n + ' contacts <small>(' + o.rate.toFixed(0) + ' / hour)</small>') +
        '</table><p class="info">Average rate counts only the time you were on the air (breaks over 30 minutes are left out). Rates are contacts per hour.</p></div>';
      /* contacts per 15 minutes, as bars */
      const slot = 15 * 6e4, t0 = Math.floor(T[0] / slot) * slot, nS = Math.min(400, Math.floor((T[T.length - 1] - t0) / slot) + 1), bins = new Array(nS).fill(0);
      T.forEach(t => { const k = Math.floor((t - t0) / slot); if (k < nS) bins[k]++; });
      const mx = Math.max(1, ...bins);
      rate += '<div class="st-card wide"><h3>Contacts every 15 minutes</h3><div class="st-spark" role="img" aria-label="Contacts per 15 minutes">' + bins.map((b, k) => '<i style="height:' + (b / mx * 100).toFixed(0) + '%" title="' + esc(DD(t0 + k * slot) + ' ' + HH(t0 + k * slot)) + 'Z: ' + b + '"></i>').join('') + '</div><p class="info">' + esc(HH(t0)) + 'Z → ' + esc(HH(t0 + nS * slot)) + 'Z · busiest 15 minutes: ' + mx + ' contacts</p></div>';
    }
    const hours = tally(r => { const t = A.when(r); return t == null ? '' : HH(t).slice(0, 2) + 'Z'; }).sort((a, b) => a[0].localeCompare(b[0]));
    /* distances from my grid / position */
    const my = recs.map(r => A.ll(r, true)).find(Boolean) || A.gridLL(S.mygrid);
    let far = '';
    if (my) { const D = recs.map(r => { const p = A.ll(r); return p ? { c: r.CALL, d: A.km(A.ll(r, true) || my, p) } : null; }).filter(Boolean);
      if (D.length) { D.sort((a, b) => b.d - a.d); const mi = k => (k * 0.621371); tiles.push(['Farthest', esc(D[0].c || '') + ' · ' + num(Math.round(mi(D[0].d))) + ' mi']); tiles.push(['Average distance', num(Math.round(mi(D.reduce((s, x) => s + x.d, 0) / D.length))) + ' mi']); tiles.push(['Total distance', num(Math.round(mi(D.reduce((s, x) => s + x.d, 0)))) + ' mi']); } }
    el.innerHTML = '<div class="st-tiles">' + tiles.map(t => '<div class="st-tile"><b>' + t[1] + '</b><span>' + esc(t[0]) + '</span></div>').join('') + '</div>' + rate +
      '<div class="st-grid">' + table('By band', tally(r => String(r.BAND || A.bandOf(r.FREQ) || '').toLowerCase()), N) + table('By mode', tally(r => String(r.SUBMODE || r.MODE || '').toUpperCase()), N) +
      table('By hour (UTC)', hours) + table('By day (UTC)', tally(r => /^\d{8}$/.test(r.QSO_DATE || '') ? r.QSO_DATE.slice(0, 4) + '-' + r.QSO_DATE.slice(4, 6) + '-' + r.QSO_DATE.slice(6) : '').sort((a, b) => a[0].localeCompare(b[0]))) +
      table('States / provinces', tally(r => String(r.STATE || '').toUpperCase()).slice(0, 60)) + table('Countries', tally(r => r.COUNTRY || '').slice(0, 40)) +
      table('Their parks (park to park)', tally(r => String(r.SIG_INFO || r.POTA_REF || '').toUpperCase()).slice(0, 40)) + table('My parks', tally(r => String(r.MY_SIG_INFO || r.MY_POTA_REF || '').toUpperCase())) +
      table('Station / operator', tally(r => String(r.OPERATOR || r.STATION_CALLSIGN || '').toUpperCase())) + table('Worked most', tally(r => String(r.CALL || '').toUpperCase()).filter(x => x[1] > 1).slice(0, 20)) + '</div>';
  }

  /* ---------- map ---------- */
  const BCOL = { '160m': '#7b3294', '80m': '#c2a5cf', '60m': '#9e9ac8', '40m': '#2c7fb8', '30m': '#41b6c4', '20m': '#d7301f', '17m': '#fc8d59', '15m': '#fdae61', '12m': '#a6d96a', '10m': '#1a9850', '6m': '#e7298a', '2m': '#666', '70cm': '#333' };
  /* Leaflet from unpkg, the same copy every other KPC map uses (the cdnjs '.min' name did not exist: Brandon Oct 31 'the map is not working') */
  function leaflet() { return window.L ? Promise.resolve() : new Promise((res, rej) => { const c = document.createElement('link'); c.rel = 'stylesheet'; c.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'; c.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY='; c.crossOrigin = ''; document.head.appendChild(c);
    const s = document.createElement('script'); s.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'; s.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo='; s.crossOrigin = ''; s.onload = res; s.onerror = rej; document.head.appendChild(s); }); }
  /* the bar on top of the map (Brandon Oct 31 4:43 PM: 'club logo then the operator's call sign, date, qso total, states worked, dx worked, park info … hide dx if it does not apply') */
  const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const fd = d => /^\d{8}$/.test(d) ? MON[+d.slice(4, 6) - 1] + ' ' + (+d.slice(6)) + ', ' + d.slice(0, 4) : d;
  const US = /^(A[A-L]|[KNW][A-Z]?)\d/;
  function mapInfo() {
    const top = f => { const t = {}; recs.forEach(r => { const v = f(r); if (v) t[v] = (t[v] || 0) + 1; }); return Object.entries(t).sort((a, b) => b[1] - a[1]).map(x => x[0]); };
    const calls = top(r => String(r.STATION_CALLSIGN || r.OPERATOR || '').toUpperCase().trim()); if (!calls.length && S.mycall) calls.push(S.mycall);
    const ops = top(r => String(r.OPERATOR || '').toUpperCase().trim()).filter(o => !calls.includes(o));
    const ds = recs.map(r => String(r.QSO_DATE || '')).filter(d => /^\d{8}$/.test(d)).sort(), d0 = ds[0], d1 = ds[ds.length - 1];
    const home = String(top(r => r.MY_COUNTRY)[0] || '').toUpperCase() || (US.test(calls[0] || '') || !calls.length ? 'UNITED STATES OF AMERICA' : ''), homeD = String(top(r => r.MY_DXCC)[0] || (/UNITED STATES/.test(home) ? '291' : ''));
    const dx = new Set(); recs.forEach(r => { const c = String(r.COUNTRY || '').toUpperCase().trim(), dd = String(r.DXCC || '').trim(), call = String(r.CALL || '').toUpperCase();
      if (c) { if (home && c !== home && !(/UNITED STATES/.test(c) && /UNITED STATES/.test(home))) dx.add(c); }
      else if (dd) { if (homeD && dd !== homeD) dx.add('#' + dd); }
      else if (/UNITED STATES/.test(home) && call) { const base = call.split('/').sort((a, b) => b.length - a.length)[0]; if (!US.test(base)) dx.add('p:' + base.replace(/\d.*$/, '').slice(0, 2)); } });
    const states = new Set(recs.map(r => String(r.STATE || '').toUpperCase().trim()).filter(Boolean));
    const parks = top(r => String(r.MY_SIG_INFO || r.MY_POTA_REF || '').toUpperCase().trim()).flatMap(x => x.split(/[,\s]+/)).filter((v, i, a) => v && a.indexOf(v) === i);
    const p2p = recs.filter(r => r.SIG_INFO || r.POTA_REF).length;
    const items = [];
    if (d0) items.push(['Date', d0 === d1 ? fd(d0) : fd(d0) + ' – ' + fd(d1)]);
    items.push(['QSOs', num(recs.length)]);
    if (states.size) items.push(['States', num(states.size)]);
    if (dx.size) items.push(['DX', num(dx.size) + (dx.size > 1 ? ' countries' : ' country')]);
    if (parks.length) items.push([parks.length > 1 ? 'Parks' : 'Park', parks.length > 4 ? parks.slice(0, 4).join(', ') + ' +' + (parks.length - 4) : parks.join(', ')]);
    if (p2p) items.push(['Park to park', num(p2p)]);
    return { call: calls.slice(0, 3).join(' · ') || 'My log', ops: ops.slice(0, 4), items };
  }
  function mapBar() {
    const m = mapInfo();
    $('aeMBar').innerHTML = '<img src="KPC-logo.png" alt="KPC logo" width="58" height="58"><div class="t"><div class="club">KENTUCKY PORTABLE CLUB · N4KPC</div><div class="call">' + esc(m.call) + '</div>' + (m.ops.length ? '<div class="club">op ' + esc(m.ops.join(', ')) + '</div>' : '') + '</div><div class="chips">' + m.items.map(x => '<span>' + esc(x[0]) + ' <b>' + esc(x[1]) + '</b></span>').join('') + '</div>';
    return m;
  }
  /* Where to put a contact when the log has no grid / lat-lon (Brandon Oct 31 4:54 PM: 'the map shows but the qsos and lines are not there'):
     their park's pin (POTA), then the middle of their state / province. My station: MY grid, then my park's pin, then SET UP grid. */
  const STC = { AL: [32.8, -86.8], AK: [61.4, -150.5], AZ: [34.3, -111.7], AR: [34.9, -92.4], CA: [37.2, -119.5], CO: [39.0, -105.5], CT: [41.6, -72.7], DE: [39.0, -75.5], DC: [38.9, -77.0], FL: [28.6, -82.4], GA: [32.7, -83.4], HI: [20.8, -156.3], ID: [44.4, -114.6], IL: [40.0, -89.2], IN: [39.9, -86.3], IA: [42.1, -93.5], KS: [38.5, -98.4], KY: [37.5, -85.3], LA: [31.1, -92.0], ME: [45.4, -69.2], MD: [39.0, -76.8], MA: [42.3, -71.8], MI: [44.3, -85.4], MN: [46.3, -94.3], MS: [32.7, -89.7], MO: [38.4, -92.5], MT: [47.0, -109.6], NE: [41.5, -99.8], NV: [39.3, -116.6], NH: [43.7, -71.6], NJ: [40.2, -74.7], NM: [34.4, -106.1], NY: [42.9, -75.5], NC: [35.6, -79.4], ND: [47.5, -100.5], OH: [40.3, -82.8], OK: [35.6, -97.5], OR: [43.9, -120.6], PA: [40.9, -77.8], RI: [41.7, -71.5], SC: [33.9, -80.9], SD: [44.4, -100.2], TN: [35.9, -86.4], TX: [31.5, -99.3], UT: [39.3, -111.7], VT: [44.1, -72.7], VA: [37.5, -78.9], WA: [47.4, -120.5], WV: [38.6, -80.6], WI: [44.6, -89.9], WY: [43.0, -107.6], PR: [18.2, -66.5],
    AB: [54.5, -114.5], BC: [53.7, -124.8], MB: [55.0, -97.4], NB: [46.6, -66.4], NL: [53.1, -61.0], NS: [45.0, -63.0], ON: [49.3, -84.5], PE: [46.4, -63.2], QC: [52.0, -71.8], SK: [54.4, -105.9], YT: [63.5, -135.7], NT: [64.8, -119.2], NU: [70.3, -95.0] };
  let PKC = {}; try { PKC = JSON.parse(localStorage.getItem('kpcAdifParks') || '{}'); } catch (e) {}
  const refOf = (r, mine) => String((mine ? (r.MY_SIG_INFO || r.MY_POTA_REF) : (r.SIG_INFO || r.POTA_REF)) || '').toUpperCase().split(/[,\s]+/)[0];
  async function parkPins() {
    const need = [...new Set(recs.flatMap(r => [refOf(r), refOf(r, true)]).filter(x => /^[A-Z0-9]{1,4}-\d{4,5}$/.test(x) && !(x in PKC)))].slice(0, 60);
    await Promise.all(need.map(ref => fetch('https://api.pota.app/park/' + encodeURIComponent(ref)).then(r => r.ok ? r.json() : null).then(j => { PKC[ref] = j && isFinite(+j.latitude) && isFinite(+j.longitude) && j.latitude !== null ? [+j.latitude, +j.longitude] : 0; }).catch(() => {})));
    if (need.length) try { localStorage.setItem('kpcAdifParks', JSON.stringify(PKC)); } catch (e) {}
  }
  function placeThem(r) { const p = A.ll(r); if (p) return [p, 'grid']; const k = PKC[refOf(r)]; if (k) return [k, 'park']; const st = STC[String(r.STATE || r.VE_PROV || '').toUpperCase().trim()]; return st ? [st, 'state'] : [null, '']; }
  function placeMe(r, def) { return A.ll(r, true) || PKC[refOf(r, true)] || def || null; }
  let DRAW = null;
  function drawMap() {
    mapBar();
    Promise.all([leaflet(), parkPins()]).then(() => {
      if (!map) { map = L.map('aeMap', { zoomControl: true }).setView([38, -90], 4); L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, crossOrigin: 'anonymous', attribution: '© OpenStreetMap contributors' }).addTo(map); mapL = L.layerGroup().addTo(map); }
      setTimeout(() => map.invalidateSize(), 50); mapL.clearLayers();
      const myDef = A.gridLL(S.mygrid), pts = [], bands = {}; let have = 0; DRAW = { lines: [], dots: [], mine: [], bands };
      const lines = $('aeLines').checked;
      const how = { grid: 0, park: 0, state: 0 };
      recs.forEach((r, i) => { const [p, hw] = placeThem(r); if (!p) return; have++; how[hw]++; const me = placeMe(r, myDef), b = String(r.BAND || A.bandOf(r.FREQ) || '').toLowerCase(), c = BCOL[b] || '#d5a63a'; bands[b] = c;
        if (me && lines) { L.polyline([me, p], { color: c, weight: 1.5, opacity: .55, interactive: false }).addTo(mapL); DRAW.lines.push([me, p, c]); }
        DRAW.dots.push([p, c, hw]);
        L.circleMarker(p, { radius: hw === 'state' ? 5 : 6, color: hw === 'state' ? c : '#111', weight: hw === 'state' ? 2 : 1, fillColor: c, fillOpacity: hw === 'state' ? .35 : .95 }).bindPopup('<b>' + esc(r.CALL || '') + '</b> ' + esc(r.NAME || '') + '<br>' + esc([r.QSO_DATE, r.TIME_ON && r.TIME_ON.slice(0, 4) + 'Z', b, r.SUBMODE || r.MODE].filter(Boolean).join(' · ')) + (r.STATE ? '<br>' + esc(r.STATE) : '') + (r.SIG_INFO ? '<br>Park ' + esc(r.SIG_INFO) : '') + (me ? '<br>' + num(Math.round(A.km(me, p) * 0.621371)) + ' mi' : '') + '<br><a href="#" data-row="' + i + '">EDIT THIS CONTACT</a>').addTo(mapL); pts.push(p); });
      const mine = [...new Set(recs.map(r => { const m = A.ll(r, true) || PKC[refOf(r, true)]; return m && m.join(','); }).filter(Boolean))].map(s => s.split(',').map(Number)); if (!mine.length && myDef) mine.push(myDef);
      mine.forEach(m => { L.marker(m, { icon: L.divIcon({ className: '', html: '<span class="ae-me">★</span>', iconSize: [22, 22], iconAnchor: [11, 11] }) }).bindPopup('My station').addTo(mapL); pts.push(m); DRAW.mine.push(m); });
      if (pts.length) map.fitBounds(L.latLngBounds(pts), { padding: [24, 24], maxZoom: 8 });
      $('aeMapN').innerHTML = num(have) + ' of ' + num(recs.length) + ' contacts on the map' + (how.park || how.state ? ' (' + [how.grid && num(how.grid) + ' by grid square', how.park && num(how.park) + ' at their park', how.state && num(how.state) + ' in the middle of their state: faint dots, rough'].filter(Boolean).join(', ') + ')' : '') + '.' + (have < recs.length ? ' The rest have no grid square, park or state: add one to see them.' : '') + (mine.length ? '' : ' Set MY grid in ⚙ SET UP (or MY_GRIDSQUARE) to draw lines from you.') +
        '<span class="ae-key">' + Object.entries(bands).map(([b, c]) => '<span><i style="background:' + c + '"></i>' + esc(b || '?') + '</span>').join('') + '</span>';
    }).catch(() => { $('aeMapN').textContent = 'The map could not load. Check your signal and tap MAP again.'; });
  }
  /* SAVE MAP AS A PICTURE: the bar + the map tiles + lines, dots, my star + the band key, drawn on one canvas → PNG */
  function loadImg(src) { return new Promise(res => { const i = new Image(); i.onload = () => res(i); i.onerror = () => res(null); i.src = src; }); }
  function wrapText(c, t, maxW) { const w = t.split(' '), out = []; let l = ''; w.forEach(x => { const n = l ? l + ' ' + x : x; if (c.measureText(n).width > maxW && l) { out.push(l); l = x; } else l = n; }); if (l) out.push(l); return out; }
  const msay = t => { $('aeMapMsg').textContent = t; };
  async function saveMap() {
    if (!map || !DRAW) { msay('Open the MAP tab first.'); return; }
    const box = $('aeMap'), R = box.getBoundingClientRect(), W = Math.round(R.width), H = Math.round(R.height), k = 2, m = mapInfo(), logo = await loadImg('KPC-logo.png');
    const meas = document.createElement('canvas').getContext('2d'); meas.font = '700 15px Arial';
    /* chips laid out in rows under the call */
    const chips = m.items.map(x => x[0] + ': ' + x[1]), rows = [[]]; let rw = 0; const cw = t => meas.measureText(t).width + 26, maxW = W - 28;
    chips.forEach(t => { const w = cw(t); if (rw + w > maxW && rows[rows.length - 1].length) { rows.push([]); rw = 0; } rows[rows.length - 1].push(t); rw += w + 8; });
    const barH = 92 + (m.ops.length ? 18 : 0) + rows.length * 34, keyH = 58, cv = document.createElement('canvas'); cv.width = W * k; cv.height = (barH + H + keyH) * k;
    const c = cv.getContext('2d'); c.scale(k, k);
    const g = c.createLinearGradient(0, 0, W, barH); g.addColorStop(0, '#0b0f0d'); g.addColorStop(.6, '#1d231f'); g.addColorStop(1, '#2a2414'); c.fillStyle = g; c.fillRect(0, 0, W, barH);
    c.fillStyle = '#d5a63a'; c.fillRect(0, barH - 4, W, 4);
    if (logo) { c.save(); c.beginPath(); c.arc(46, 46, 32, 0, 7); c.clip(); c.drawImage(logo, 14, 14, 64, 64); c.restore(); c.strokeStyle = '#d5a63a'; c.lineWidth = 2; c.beginPath(); c.arc(46, 46, 33, 0, 7); c.stroke(); }
    c.fillStyle = '#f0c96b'; c.font = '14px Georgia, serif'; c.fillText('KENTUCKY PORTABLE CLUB · N4KPC', 92, 34);
    c.fillStyle = '#f3ecd9'; c.font = '900 30px Arial'; c.fillText(m.call, 92, 68, W - 104);
    let y = 84; if (m.ops.length) { c.fillStyle = '#f0c96b'; c.font = '13px Georgia, serif'; c.fillText('op ' + m.ops.join(', '), 92, y + 2); y += 18; }
    c.font = '700 15px Arial'; rows.forEach(row => { let x = 14; row.forEach(t => { const w = cw(t); c.fillStyle = 'rgba(213,166,58,.18)'; c.strokeStyle = 'rgba(240,201,107,.6)'; c.lineWidth = 1; c.beginPath(); c.roundRect(x, y, w, 28, 14); c.fill(); c.stroke(); c.fillStyle = '#f3ecd9'; c.fillText(t, x + 13, y + 19); x += w + 8; }); y += 34; });
    /* the map */
    c.save(); c.translate(0, barH); c.fillStyle = '#aad3df'; c.fillRect(0, 0, W, H); c.beginPath(); c.rect(0, 0, W, H); c.clip();
    box.querySelectorAll('.leaflet-tile-pane img.leaflet-tile').forEach(im => { if (!im.complete || !im.naturalWidth) return; const r = im.getBoundingClientRect(); c.drawImage(im, r.left - R.left, r.top - R.top, r.width, r.height); });
    const P = ll => map.latLngToContainerPoint(ll);
    DRAW.lines.forEach(([a, b, col]) => { const p = P(a), q = P(b); c.strokeStyle = col; c.globalAlpha = .6; c.lineWidth = 1.5; c.beginPath(); c.moveTo(p.x, p.y); c.lineTo(q.x, q.y); c.stroke(); }); c.globalAlpha = 1;
    DRAW.dots.forEach(([a, col, hw]) => { const p = P(a), st = hw === 'state'; c.globalAlpha = st ? .45 : 1; c.fillStyle = col; c.strokeStyle = st ? col : '#111'; c.lineWidth = st ? 2 : 1; c.beginPath(); c.arc(p.x, p.y, st ? 5 : 6, 0, 7); c.fill(); c.globalAlpha = 1; c.stroke(); });
    DRAW.mine.forEach(a => { const p = P(a); c.font = '900 26px Arial'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.lineWidth = 4; c.strokeStyle = '#111'; c.strokeText('★', p.x, p.y); c.fillStyle = '#ffd34d'; c.fillText('★', p.x, p.y); c.textAlign = 'left'; c.textBaseline = 'alphabetic'; });
    c.restore();
    /* band key + credit */
    c.fillStyle = '#0b0f0d'; c.fillRect(0, barH + H, W, keyH); c.font = '700 13px Arial'; let x = 14; const ky = barH + H + 24;
    Object.entries(DRAW.bands).forEach(([b, col]) => { c.fillStyle = col; c.beginPath(); c.arc(x + 5, ky - 4, 5, 0, 7); c.fill(); c.fillStyle = '#f3ecd9'; c.fillText(b || '?', x + 14, ky); x += c.measureText(b || '?').width + 30; });
    c.font = '11px Arial'; c.fillStyle = '#bdb6a3'; c.fillText('Map © OpenStreetMap contributors · Kentucky Portable Club', 14, ky + 22);
    const name = (m.call.split(' ')[0] || 'log').replace(/[^A-Z0-9-]/gi, '-') + '-map' + (m.items[0] && m.items[0][0] === 'Date' ? '-' + (recs.map(r => r.QSO_DATE || '').filter(Boolean).sort()[0] || '') : '') + '.png';
    try {
      cv.toBlob(bl => { if (!bl) { msay('The picture could not be made on this device.'); return; } const u = URL.createObjectURL(bl), a = document.createElement('a'); a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 4000); msay('Saved ' + name + '.'); }, 'image/png');
    } catch (e) { msay('The map picture could not be saved here (the map pictures did not allow it). Try again once the map has finished loading.'); }
  }

  /* ---------- tabs ---------- */
  function setTab(t) {
    tab = t; ['edit', 'check', 'stats', 'map', 'setup'].forEach(k => { const p = $('aeP-' + k); if (p) p.hidden = k !== t; const b = document.querySelector('#aeTabs [data-tab="' + k + '"]'); if (b) { b.classList.toggle('on', k === t); b.setAttribute('aria-selected', String(k === t)); } });
    if (t === 'stats') stats(); if (t === 'map') drawMap();
  }

  /* ---------- events ---------- */
  $('aeMapSave').addEventListener('click', saveMap);
  document.addEventListener('click', e => { const b = e.target.closest('[data-tab]'); if (b && $('ae').contains(b)) setTab(b.dataset.tab); });
  const readFiles = (files, add) => { [...files].forEach((f, k) => { const rd = new FileReader(); rd.onload = () => { const t = String(rd.result || ''); if (/\.csv$/i.test(f.name)) { const R = csvParse(t); const fake = A.write('', R); load(fake, f.name, add || k > 0); } else load(t, f.name, add || k > 0); }; rd.readAsText(f); }); };
  $('aeFile').addEventListener('change', () => { readFiles($('aeFile').files, false); $('aeFile').value = ''; });
  $('aeMerge').addEventListener('change', () => { readFiles($('aeMerge').files, true); $('aeMerge').value = ''; });
  $('aeIss').addEventListener('click', e => {
    const f = e.target.closest('[data-fix]'), g = e.target.closest('[data-go]');
    if (f) { const x = issues[+f.dataset.fix]; if (x.fix.kind === 'split') return potaSave(); snap(); A.fix(recs, x); say('Fixed: ' + x.msg); run(); }
    if (g) goRow(+g.dataset.go);
  });
  function goRow(i) { setTab('edit'); filt = ''; $('aeFilt').value = ''; const pos = shown().indexOf(i); if (pos >= 0) page = Math.floor(pos / PAGE); grid();
    const tr = $('aeGrid').querySelector('tr[data-r="' + i + '"]'); if (tr) { $('aeGrid').querySelectorAll('tr.hit').forEach(t => t.classList.remove('hit')); tr.classList.add('hit'); tr.scrollIntoView({ block: 'center', behavior: 'smooth' }); } }
  $('aeMap').addEventListener('click', e => { const a = e.target.closest('[data-row]'); if (a) { e.preventDefault(); goRow(+a.dataset.row); } });
  /* Brandon 4:29 PM: 'when I add a column etc make it easy to add to all rows … adif master has a good set up': tap a column name = its menu */
  let CM = '';
  $('aeGrid').addEventListener('click', e => { const s = e.target.closest('[data-sort]'); if (!s) return; CM = s.dataset.sort; $('aeCmT').textContent = CM; $('aeCmD').textContent = (A.FIELDS[CM] || 'ADIF field') + (TICK.size ? ' · ' + TICK.size + ' ticked contacts' : ' · every contact'); $('aeCmV').value = ''; SHEETS.forEach(x => { $(x).hidden = x !== 'aeColMenu'; }); $('aeColMenu').scrollIntoView({ block: 'nearest', behavior: 'smooth' }); });
  $('aeColMenu').addEventListener('click', e => {
    const b = e.target.closest('[data-cm]'); if (!b || !CM) return; const a = b.dataset.cm, v = $('aeCmV').value.trim(), T = TICK.size ? [...TICK] : recs.map((r, i) => i); let n = 0;
    if (a === 'asc' || a === 'desc') { sortBy = CM; sortDir = a === 'asc' ? 1 : -1; return grid(); }
    if (a === 'hide') { hidden.add(CM); $('aeColMenu').hidden = true; return grid(); }
    if (a === 'left' || a === 'right') { const o = allCols(), k = o.indexOf(CM), j = a === 'left' ? k - 1 : k + 1; if (j >= 0 && j < o.length) { o.splice(k, 1); o.splice(j, 0, CM); order = o; } return grid(); }
    if (a === 'rename') { SHEETS.forEach(x => { $(x).hidden = x !== 'aeCols'; }); fieldLists(); $('aeRenF').value = CM; $('aeRenRow').hidden = false; $('aeRenTo').focus(); return; }
    if (a === 'drop') { if (!b.dataset.sure) { b.dataset.sure = '1'; b.textContent = 'TAP AGAIN TO DELETE ' + CM; return; } b.dataset.sure = ''; b.textContent = 'DELETE FIELD'; snap(); recs.forEach(r => { delete r[CM]; }); extra = extra.filter(x => x !== CM); $('aeColMenu').hidden = true; say(CM + ' removed from every contact.'); return run(); }
    if ((a === 'set' || a === 'fill') && !v) return say('Type the value first.', true);
    snap();
    if (a === 'down') { const ix = shown(); let last = ''; ix.forEach(i => { if (!T.includes(i)) return; const cur = recs[i][CM]; if (cur) last = cur; else if (last) { recs[i][CM] = last; n++; } }); }
    else T.forEach(i => { const r = recs[i]; if (a === 'set') { r[CM] = v; n++; } else if (a === 'fill') { if (!r[CM]) { r[CM] = v; n++; } } else if (a === 'upper') { if (r[CM] && r[CM] !== String(r[CM]).toUpperCase()) { r[CM] = String(r[CM]).toUpperCase(); n++; } } else if (a === 'clear') { if (CM in r) { delete r[CM]; n++; } } });
    say(CM + ': ' + n + ' contact' + (n === 1 ? '' : 's') + ' changed.'); run();
  });
  $('aeGrid').addEventListener('change', e => {
    const t = e.target;
    if (t.matches('[data-tick]')) { const i = +t.dataset.tick; if (t.checked) TICK.add(i); else TICK.delete(i); $('aeDel').disabled = $('aeCopy').disabled = !TICK.size; $('aeCount').textContent = $('aeCount').textContent.replace(/ · \d[\d,]* ticked/, '') + (TICK.size ? ' · ' + TICK.size + ' ticked' : ''); return; }
    if (t.id === 'aeAll') { shown().forEach(i => { if (t.checked) TICK.add(i); else TICK.delete(i); }); return grid(); }
    const c = t.dataset.c, i = +t.closest('tr').dataset.r; if (!c || !recs[i]) return;
    snap(); const v = t.value.trim(); if (v) recs[i][c] = v; else delete recs[i][c]; run();
  });
  $('aeFilt').addEventListener('input', () => { filt = $('aeFilt').value.trim(); page = 0; grid(); });
  $('aePrev').addEventListener('click', () => { page--; grid(); }); $('aeNext').addEventListener('click', () => { page++; grid(); });
  $('aeFixAll').addEventListener('click', () => { snap(); const n = A.fixAll(recs, opt()); say(n ? n + ' fix' + (n > 1 ? 'es' : '') + ' made. Anything left needs a person: tap SHOW to find it.' : 'Nothing I can fix by myself. Tap SHOW on each line to edit it.'); run(); });
  const SHEETS = ['aeBulk', 'aeFind', 'aeCols', 'aeColMenu'];
  const sheet = id => SHEETS.forEach(s => { $(s).hidden = s !== id || !$(s).hidden; });
  $('aeBulkBtn').addEventListener('click', () => { sheet('aeBulk'); $('aeBT').value = TICK.size ? 'tick' : 'all'; });
  $('aeFindBtn').addEventListener('click', () => sheet('aeFind')); $('aeColsBtn').addEventListener('click', () => sheet('aeCols'));
  document.querySelectorAll('#ae [data-close]').forEach(b => b.addEventListener('click', () => { $(b.dataset.close).hidden = true; }));
  $('aeBA').addEventListener('change', () => { const a = $('aeBA').value; $('aeBV').hidden = !['set', 'fill', 'shift'].includes(a); $('aeBFrom').hidden = a !== 'copy'; $('aeBF').disabled = a === 'shift' || a === 'band'; $('aeBV').placeholder = a === 'shift' ? 'Minutes, like 60 or -300 (5 h back)' : 'Value'; });
  $('aeBGo').addEventListener('click', bulk);
  $('aeFindGo').addEventListener('click', () => { const f = $('aeFindF').value, a = $('aeFindA').value, b = $('aeFindB').value, cs = $('aeFindC').checked, whole = $('aeFindW').checked; if (!a) return say('Type what to find.', true);
    snap(); let n = 0; const T = $('aeFindT').value === 'tick' ? [...TICK] : recs.map((r, i) => i);
    T.forEach(i => { const r = recs[i]; Object.keys(r).forEach(k => { if (f !== '*' && f !== k) return; const v = String(r[k]);
      if (whole) { if (cs ? v === a : v.toUpperCase() === a.toUpperCase()) { r[k] = b; n++; } }
      else { const re = new RegExp(a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), cs ? 'g' : 'gi'); if (re.test(v)) { r[k] = v.replace(re, b); n++; } } }); });
    say(n + ' replaced.'); run(); });
  $('aeColList').addEventListener('change', e => { const c = e.target.dataset.show; if (!c) return; if (e.target.checked) hidden.delete(c); else hidden.add(c); grid(); });
  $('aeColList').addEventListener('click', e => {
    const up = e.target.dataset.up, ren = e.target.dataset.ren, drop = e.target.dataset.drop;
    if (up) { const o = allCols(), k = o.indexOf(up); if (k > 0) { o.splice(k, 1); o.splice(k - 1, 0, up); order = o; grid(); } }
    if (ren) { $('aeRenF').value = ren; $('aeRenRow').hidden = false; $('aeRenTo').focus(); }
    if (drop) { if (!e.target.dataset.sure) { e.target.dataset.sure = '1'; e.target.textContent = 'TAP AGAIN TO DELETE'; return; } snap(); recs.forEach(r => { delete r[drop]; }); extra = extra.filter(x => x !== drop); say(drop + ' removed from every contact.'); run(); }
  });
  $('aeRenGo').addEventListener('click', () => { const f = $('aeRenF').value, to = $('aeRenTo').value.trim().toUpperCase().replace(/[^A-Z0-9_]/g, ''); if (!to || to === f) return; snap(); recs.forEach(r => { if (f in r) { r[to] = r[f]; delete r[f]; } }); if (order) order = order.map(x => x === f ? to : x); $('aeRenTo').value = ''; $('aeRenRow').hidden = true; say(f + ' renamed to ' + to + '.'); run(); });
  $('aeAddCol').addEventListener('click', () => { const c = ($('aeNewColT').value.trim() || $('aeNewCol').value).toUpperCase().replace(/[^A-Z0-9_]/g, ''), v = $('aeNewColV').value.trim(); if (!c) return;
    if (!extra.includes(c)) extra.push(c); hidden.delete(c); $('aeNewColT').value = ''; $('aeNewColV').value = '';
    if (v) { snap(); const T = TICK.size ? [...TICK] : recs.map((r, i) => i); T.forEach(i => { recs[i][c] = v; }); say(c + ' added and set to "' + v + '" on ' + T.length + ' contact' + (T.length > 1 ? 's' : '') + '.'); run(); }
    else { grid(); say(c + ' added as a column. Tap its name for SET FOR ALL, or type in the cells.'); } });
  $('aeNewColBtn').addEventListener('click', () => { SHEETS.forEach(x => { $(x).hidden = x !== 'aeCols'; }); fieldLists(); $('aeNewColV').focus(); });
  $('aeCopy').addEventListener('click', () => { const t = [...TICK].sort((a, b) => a - b); if (!t.length) return; snap(); t.forEach(i => recs.push(Object.assign({}, recs[i]))); TICK.clear(); say(t.length + ' contact' + (t.length > 1 ? 's' : '') + ' copied to the end of the log.'); run(); });
  $('aeShowAll').addEventListener('click', () => { hidden = new Set(); order = null; grid(); });
  $('aeAdd').addEventListener('click', () => { snap(); const last = recs[recs.length - 1] || {}, r = {}; ['QSO_DATE', 'BAND', 'FREQ', 'MODE', 'SUBMODE', 'STATION_CALLSIGN', 'OPERATOR', 'MY_SIG', 'MY_SIG_INFO', 'MY_GRIDSQUARE', 'TX_PWR'].forEach(k => { if (last[k]) r[k] = last[k]; }); recs.push(r); filt = ''; $('aeFilt').value = ''; sortBy = null; page = Math.floor((recs.length - 1) / PAGE); run(); setTab('edit');
    const tr = $('aeGrid').querySelector('tr[data-r="' + (recs.length - 1) + '"]'); if (tr) { tr.scrollIntoView({ block: 'center' }); const c = tr.querySelector('[data-c=CALL]'); if (c) c.focus(); } });
  $('aeDel').addEventListener('click', () => { const t = [...TICK]; if (!t.length) return; snap(); recs = recs.filter((r, i) => !TICK.has(i)); TICK.clear(); say(t.length + ' contact' + (t.length > 1 ? 's' : '') + ' deleted.'); run(); });
  $('aeDup').addEventListener('click', () => { const d = dupes(); TICK.clear(); d.forEach(i => TICK.add(i)); say(d.length ? d.length + ' duplicate' + (d.length > 1 ? 's' : '') + ' ticked (the first of each is kept). DELETE TICKED removes them.' : 'No duplicates (same call, day, band, mode and park).'); grid(); });
  $('aeEmptyF').addEventListener('click', () => { snap(); let n = 0; recs.forEach(r => Object.keys(r).forEach(k => { if (String(r[k]).trim() === '') { delete r[k]; n++; } })); say(n + ' empty field' + (n === 1 ? '' : 's') + ' removed.'); run(); });
  $('aeUndo').addEventListener('click', () => { const u = undo.pop(); if (!u) return; redo.push(JSON.stringify(recs)); recs = JSON.parse(u); TICK.clear(); $('aeUndo').disabled = !undo.length; $('aeRedo').disabled = false; say('Undone.'); run(); });
  $('aeRedo').addEventListener('click', () => { const u = redo.pop(); if (!u) return; undo.push(JSON.stringify(recs)); recs = JSON.parse(u); TICK.clear(); $('aeRedo').disabled = !redo.length; $('aeUndo').disabled = false; say('Redone.'); run(); });
  $('aeSave').addEventListener('click', () => { download(A.write(header, recs), base() + '-checked.adi'); say('Saved ' + base() + '-checked.adi.'); });
  $('aeSaveT').addEventListener('click', () => { const T = [...TICK].sort((a, b) => a - b).map(i => recs[i]); if (!T.length) return say('Tick some contacts first.', true); download(A.write(header, T), base() + '-ticked.adi'); say(T.length + ' ticked contacts saved.'); });
  $('aeCsv').addEventListener('click', () => { download(csvOut(recs), base() + '.csv', 'text/csv'); say('Saved ' + base() + '.csv (opens in Excel / Sheets).'); });
  $('aePota').addEventListener('click', potaSave);
  $('aeSend').addEventListener('click', () => { try { sessionStorage.setItem('kpcAdifBack', JSON.stringify({ name: base() + '-checked.adi', text: A.write(header, recs) })); } catch (e) { return say('This browser would not hand the log over; use SAVE ADIF, then pick that file in the uploader.', true); } location.href = 'kpc-club.html#qrzup'; });
  $('aeLines').addEventListener('change', drawMap);
  /* settings */
  function fillS() { $('aeMy').value = S.mycall || ''; $('aeMyG').value = S.mygrid || ''; $('aeSQ').checked = !!S.qrzOn; $('aeSQc').value = S.qrz || ''; $('aeSP').checked = !!S.potaOn; $('aeSSplit').value = S.potaSplit; $('aeSName').value = S.potaName; $('aeSSig').checked = !!S.potaAddSig; $('aeSP2P').checked = !!S.p2p; }
  $('aeP-setup').addEventListener('change', () => { S.mycall = $('aeMy').value.trim().toUpperCase(); S.mygrid = $('aeMyG').value.trim(); S.qrzOn = $('aeSQ').checked; S.qrz = $('aeSQc').value.trim().toUpperCase(); S.potaOn = $('aeSP').checked; S.potaSplit = $('aeSSplit').value; S.potaName = $('aeSName').value.trim() || DEF.potaName; S.potaAddSig = $('aeSSig').checked; S.p2p = $('aeSP2P').checked; saveS(); if (recs.length) run(); $('aeSetMsg').textContent = 'Saved on this device.'; });
  document.querySelectorAll('#ae [data-qrzcall]').forEach(b => b.addEventListener('click', () => { $('aeSQc').value = b.dataset.qrzcall === 'me' ? ($('aeMy').value.trim().toUpperCase() || '') : b.dataset.qrzcall; $('aeSQ').checked = true; $('aeP-setup').dispatchEvent(new Event('change')); }));
  fillS();
  /* a log handed over by the N4KPC uploader: check it for N4KPC */
  try { const h = JSON.parse(sessionStorage.getItem('kpcAdifHand') || 'null'); if (h && h.text) { sessionStorage.removeItem('kpcAdifHand'); S.qrzOn = true; S.qrz = 'N4KPC'; fillS(); load(h.text, h.name); setTab('check'); } } catch (e) {}
  setTab(tab); grid();
})();
