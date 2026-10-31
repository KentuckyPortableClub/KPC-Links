/* KPC ADIF Log Checker & Editor (kpc-adif.html, members only; Brandon Oct 31: 'a log checker for pota and qrz and then an
   adif editor like adif master, all just buttons, I like the clean look'). Uses KPCAdif (kpc-adif-lib.js). The log stays
   in this browser; the N4KPC uploader hands a file over in sessionStorage 'kpcAdifHand' and gets it back in 'kpcAdifBack'. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id), A = window.KPCAdif;
  if (!$('ae') || !A) return;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const FIRST = ['CALL', 'QSO_DATE', 'TIME_ON', 'BAND', 'FREQ', 'MODE', 'SUBMODE', 'RST_SENT', 'RST_RCVD', 'STATION_CALLSIGN', 'OPERATOR', 'MY_SIG', 'MY_SIG_INFO', 'SIG', 'SIG_INFO', 'NAME', 'STATE', 'GRIDSQUARE', 'COMMENT'];
  let header = '', recs = [], name = '', issues = [], undo = [], extra = [];
  const opt = { qrz: 'N4KPC', pota: true };
  const say = (t, bad) => { const m = $('aeMsg'); m.textContent = t || ''; m.style.color = bad ? '#d0452e' : ''; };
  const snap = () => { undo.push(JSON.stringify(recs)); if (undo.length > 30) undo.shift(); $('aeUndo').disabled = false; };
  function cols() {
    const have = new Set(); recs.forEach(r => Object.keys(r).forEach(k => have.add(k))); extra.forEach(k => have.add(k));
    const base = FIRST.filter(k => have.has(k) || ['CALL', 'QSO_DATE', 'TIME_ON', 'BAND', 'MODE', 'STATION_CALLSIGN'].includes(k) || (opt.pota && k === 'MY_SIG_INFO'));
    return base.concat([...have].filter(k => !FIRST.includes(k)).sort());
  }
  function run() {
    issues = A.check(recs, { qrz: opt.qrz, pota: opt.pota });
    const e = issues.filter(x => x.level === 'error').length, w = issues.length - e;
    $('aeSum').innerHTML = recs.length ? '<span class="pill">' + recs.length + ' contact' + (recs.length > 1 ? 's' : '') + '</span>' +
      (issues.length ? (e ? '<span class="pill err">✕ ' + e + ' problem' + (e > 1 ? 's' : '') + '</span>' : '') + (w ? '<span class="pill wrn">⚠ ' + w + ' to look at</span>' : '') : '<span class="pill ok">✓ Log looks good' + (opt.qrz ? ' for QRZ' : '') + (opt.pota ? (opt.qrz ? ' and' : ' for') + ' POTA' : '') + '</span>') : '';
    const L = $('aeIss'); L.hidden = !issues.length;
    L.innerHTML = issues.slice(0, 400).map((x, k) => '<li><b class="' + (x.level === 'error' ? 'e' : 'w') + '">' + (x.level === 'error' ? '✕' : '⚠') + ' ' + (x.i >= 0 ? 'Contact ' + (x.i + 1) : 'Whole file') + '</b><span>' + esc(x.msg) + '</span>' +
      (x.fix ? '<button type="button" data-fix="' + k + '">' + (x.fix.kind === 'delete' ? 'DELETE IT' : x.fix.kind === 'split' ? 'SPLIT BY PARK' : 'FIX') + '</button>' : '') + (x.i >= 0 ? '<button type="button" data-go="' + x.i + '">SHOW</button>' : '') + '</li>').join('') + (issues.length > 400 ? '<li>…and ' + (issues.length - 400) + ' more.</li>' : '');
    grid();
  }
  function grid() {
    const C = cols(), bad = {};
    issues.forEach(x => { if (x.i >= 0) bad[x.i + '|' + x.field] = x.level; });
    $('aeGridW').hidden = $('aeTools').hidden = !recs.length;
    $('aeGrid').innerHTML = '<thead><tr><th><input type="checkbox" id="aeAll" aria-label="Tick all"></th><th>#</th>' + C.map(c => '<th>' + esc(c) + '</th>').join('') + '</tr></thead><tbody>' +
      recs.map((r, i) => '<tr data-r="' + i + '"><td><input type="checkbox" data-tick="' + i + '" aria-label="Tick contact ' + (i + 1) + '"></td><td class="n">' + (i + 1) + '</td>' +
        C.map(c => '<td class="' + (bad[i + '|' + c] === 'error' ? 'bad' : bad[i + '|' + c] ? 'wrn' : '') + '"><input type="text" data-c="' + esc(c) + '" value="' + esc(r[c] || '') + '" aria-label="' + esc(c) + ' of contact ' + (i + 1) + '"></td>').join('') + '</tr>').join('') + '</tbody>';
    const F = ['<option value="">Pick a field</option>'].concat(C.map(c => '<option>' + esc(c) + '</option>')).join('');
    $('aeSetF').innerHTML = F; $('aeFindF').innerHTML = '<option value="*">Every field</option>' + C.map(c => '<option>' + esc(c) + '</option>').join('');
    ticks();
  }
  const ticks = () => { $('aeDel').disabled = !$('aeGrid').querySelector('[data-tick]:checked'); };
  function load(text, nm) {
    const p = A.parse(text); header = p.header; recs = p.recs; name = nm || 'log.adi'; undo = []; extra = []; $('aeUndo').disabled = true;
    $('aeName').textContent = recs.length ? 'Open: ' + name : 'No contacts found in ' + name + '. Is it an ADIF (.adi) file?';
    say(''); run();
  }
  function download(text, fn) { const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' })); a.download = fn; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500); }
  const base = () => name.replace(/\.(adi|adif)$/i, '');

  /* ---- events ---- */
  $('aeFile').addEventListener('change', () => { const f = $('aeFile').files[0]; if (!f) return; const rd = new FileReader(); rd.onload = () => load(String(rd.result || ''), f.name); rd.readAsText(f); $('aeFile').value = ''; });
  const tog = (id, key, val) => $(id).addEventListener('click', () => { opt[key] = opt[key] ? (key === 'qrz' ? '' : false) : val; $(id).classList.toggle('on', !!opt[key]); $(id).setAttribute('aria-pressed', String(!!opt[key])); if (recs.length) run(); });
  tog('aeQrz', 'qrz', 'N4KPC'); tog('aePota', 'pota', true);
  $('aeIss').addEventListener('click', e => {
    const f = e.target.closest('[data-fix]'), g = e.target.closest('[data-go]');
    if (f) { const x = issues[+f.dataset.fix]; if (x.fix.kind === 'split') return $('aeSplit').click(); snap(); A.fix(recs, x); say('Fixed: ' + x.msg); run(); }
    if (g) { const tr = $('aeGrid').querySelector('tr[data-r="' + g.dataset.go + '"]'); if (tr) { $('aeGrid').querySelectorAll('tr.hit').forEach(t => t.classList.remove('hit')); tr.classList.add('hit'); tr.scrollIntoView({ block: 'center', behavior: 'smooth' }); } }
  });
  $('aeGrid').addEventListener('change', e => {
    const t = e.target;
    if (t.matches('[data-tick]')) return ticks();
    if (t.id === 'aeAll') { $('aeGrid').querySelectorAll('[data-tick]').forEach(c => { c.checked = t.checked; }); return ticks(); }
    const c = t.dataset.c, i = +t.closest('tr').dataset.r; if (!c || !recs[i]) return;
    snap(); const v = t.value.trim(); if (v) recs[i][c] = v; else delete recs[i][c]; run();
  });
  $('aeFixAll').addEventListener('click', () => { snap(); const n = A.fixAll(recs, { qrz: opt.qrz, pota: opt.pota }); say(n ? n + ' fix' + (n > 1 ? 'es' : '') + ' made. Anything left needs a person: tap SHOW to find it.' : 'Nothing I can fix by myself. Tap SHOW on each line to edit it.'); run(); });
  const sheet = (open, ids) => ids.forEach(id => { $(id).hidden = id !== open || !$(id).hidden; });
  $('aeSetBtn').addEventListener('click', () => sheet('aeSet', ['aeSet', 'aeFind', 'aeColS'])); $('aeSetX').addEventListener('click', () => { $('aeSet').hidden = true; });
  $('aeFindBtn').addEventListener('click', () => sheet('aeFind', ['aeSet', 'aeFind', 'aeColS'])); $('aeFindX').addEventListener('click', () => { $('aeFind').hidden = true; });
  $('aeCol').addEventListener('click', () => sheet('aeColS', ['aeSet', 'aeFind', 'aeColS'])); $('aeColX').addEventListener('click', () => { $('aeColS').hidden = true; });
  $('aeSetGo').addEventListener('click', () => { const f = $('aeSetF').value, v = $('aeSetV').value.trim(); if (!f) return say('Pick a field first.', true);
    snap(); recs.forEach(r => { if (v) r[f] = v; else delete r[f]; }); say(f + (v ? ' set to "' + v + '"' : ' removed') + ' on all ' + recs.length + ' contacts.'); run(); });
  $('aeFindGo').addEventListener('click', () => { const f = $('aeFindF').value, a = $('aeFindA').value, b = $('aeFindB').value; if (!a) return say('Type what to find.', true);
    snap(); let n = 0; recs.forEach(r => Object.keys(r).forEach(k => { if ((f === '*' || f === k) && String(r[k]).includes(a)) { r[k] = String(r[k]).split(a).join(b); n++; } })); say(n + ' replaced.'); run(); });
  $('aeColGo').addEventListener('click', () => { const c = $('aeColN').value.trim().toUpperCase().replace(/[^A-Z0-9_]/g, ''); if (!c) return; if (!extra.includes(c)) extra.push(c); $('aeColN').value = ''; $('aeColS').hidden = true; grid(); });
  $('aeAdd').addEventListener('click', () => { snap(); const last = recs[recs.length - 1] || {}, r = {}; ['QSO_DATE', 'BAND', 'FREQ', 'MODE', 'SUBMODE', 'STATION_CALLSIGN', 'OPERATOR', 'MY_SIG', 'MY_SIG_INFO'].forEach(k => { if (last[k]) r[k] = last[k]; }); recs.push(r); run();
    const tr = $('aeGrid').querySelector('tr[data-r="' + (recs.length - 1) + '"]'); if (tr) { tr.scrollIntoView({ block: 'center' }); const c = tr.querySelector('[data-c=CALL]'); if (c) c.focus(); } });
  $('aeDel').addEventListener('click', () => { const t = [...$('aeGrid').querySelectorAll('[data-tick]:checked')].map(c => +c.dataset.tick); if (!t.length) return; snap(); recs = recs.filter((r, i) => !t.includes(i)); say(t.length + ' contact' + (t.length > 1 ? 's' : '') + ' deleted.'); run(); });
  $('aeUndo').addEventListener('click', () => { const u = undo.pop(); if (!u) return; recs = JSON.parse(u); $('aeUndo').disabled = !undo.length; say('Undone.'); run(); });
  $('aeSave').addEventListener('click', () => { download(A.write(header, recs), base() + '-checked.adi'); say('Saved ' + base() + '-checked.adi to your downloads.'); });
  /* POTA naming: CALL@PARK-YYYYMMDD.adi (docs.pota.app 'Submitting logs') */
  $('aeSplit').addEventListener('click', () => { const g = A.byPark(recs), ks = Object.keys(g);
    ks.forEach((k, j) => { const L = g[k], call = String(L[0].STATION_CALLSIGN || L[0].OPERATOR || 'CALL').toUpperCase().replace(/\//g, '-'), d = String(L[0].QSO_DATE || '');
      setTimeout(() => download(A.write(header, L), k === 'NO-PARK' ? base() + '-no-park.adi' : call + '@' + k + (d ? '-' + d : '') + '.adi'), j * 400); });
    say(ks.length + ' file' + (ks.length > 1 ? 's' : '') + ' saved, one per park (' + ks.join(', ') + '). Upload each one on POTA.'); });
  $('aeSend').addEventListener('click', () => { try { sessionStorage.setItem('kpcAdifBack', JSON.stringify({ name: base() + '-checked.adi', text: A.write(header, recs) })); } catch (e) { return say('This browser would not hand the log over; use SAVE ADIF, then pick that file in the uploader.', true); } location.href = 'kpc-club.html#qrzup'; });
  /* a log handed over by the N4KPC uploader */
  try { const h = JSON.parse(sessionStorage.getItem('kpcAdifHand') || 'null'); if (h && h.text) { sessionStorage.removeItem('kpcAdifHand'); load(h.text, h.name); $('aeQrz').classList.add('on'); } } catch (e) {}
})();
