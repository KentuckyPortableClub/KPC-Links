/* KPC app: ✅ CHECK & SAVE FOR POTA (to-do 10, Nov 17; Brandon: bring in features of the website's kpc-log-checker.html,
   'idk what you think is best'). Not in settings: a ✅ CHECK chip on the LOG screen (and a button in STATION → Log files),
   since that is where the log is. The log being checked = the log on the screen (KPCLog.shown()).
   CHECKS (each one on/off, kept in kpcAppChk): a real call on every contact, date + time, band (or one worked out from the
   frequency), a mode, my station call (the call QRZ and POTA match the file to), park numbers that look right, the same
   contact twice (POTA counts it once), and 10 contacts per park per UTC day for a valid activation.
   FIX ALL = the fixes that are safe to do by themselves: band from the frequency, my call as the station call, calls in
   capitals with no spaces. Nothing is deleted. Doubles are only shown.
   SAVE FOR POTA: one file per park + call (POTA's rule), or per park + call + UTC day, or everything in one file; file
   names {CALL}@{PARK}-{YYYYMMDD}.adi (what POTA's own files look like) or "{CALL} {PARK} {DATE} {STATE}.adi".
   The ADIF itself is KPCLog.adif (QRZ / POTA rules: FT4 + JS8 as MFSK + SUBMODE, MY_SIG / MY_SIG_INFO, OPERATOR …).
   RATES + STATS: contacts per band and mode, the best 60 minutes. The full spreadsheet-style editor (column menus, find &
   replace) stays on the website: 🌐 OPEN THE WEBSITE CHECKER opens it, and the file saved here opens there. Everything stays
   on the device. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id);
  if (!AP || !G.KPCLog) return;
  const L = G.KPCLog, esc = AP.esc;
  const SITE = 'https://kentuckyportableclub.github.io/KPC-Links/kpc-log-checker.html', UPLOAD = 'https://pota.app/#/user/logs';
  const C = Object.assign({ call: true, time: true, band: true, mode: true, station: true, park: true, dupe: true, ten: true, split: 'park', name: 'pota' },
    (() => { try { return JSON.parse(localStorage.getItem('kpcAppChk') || '{}'); } catch (e) { return {}; } })());
  const cSave = () => { try { localStorage.setItem('kpcAppChk', JSON.stringify(C)); } catch (e) {} };
  const CHECKS = [['call', 'A real call on every contact'], ['time', 'Date and time'], ['band', 'Band (or frequency)'], ['mode', 'Mode'],
    ['station', 'My call as the station call (what QRZ and POTA match)'], ['park', 'Park numbers look right'], ['dupe', 'Same contact twice'], ['ten', '10 contacts per park per UTC day']];
  const callOk = c => /^([A-Z0-9]{1,4}\/)?[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}[A-Z](\/[A-Z0-9]{1,4})?$/.test(String(c || ''));
  const parkOk = r => /^[A-Z0-9]{1,3}-\d{4,5}$/.test(r) || /FF-\d{4}$/.test(r) || /^[A-Z0-9]+\/[A-Z]{2}-\d{3}$/.test(r);
  const isPota = r => /^[A-Z0-9]{1,3}-\d{4,5}$/.test(r);
  const day = t => new Date(t).toISOString().slice(0, 10);
  const bandOf = k => (L.band ? L.band(k) : '') || '';
  const meCall = () => String(AP.myCall ? AP.myCall() : (AP.me().call || '')).toUpperCase();
  const stCall = q => String(q.station || meCall()).toUpperCase();
  const list = () => (L.shown ? L.shown() : L.qs()) || [];

  /* ---------- the checks: [{k, q, msg, fix?}] ---------- */
  function check(Q) {
    const out = [], me = meCall(), seen = {};
    for (const q of Q) {
      const call = String(q.call || '');
      if (C.call) {
        if (!call) out.push({ k: 'call', q, msg: 'no call' });
        else if (call !== call.toUpperCase().replace(/\s+/g, '')) out.push({ k: 'call', q, msg: 'call in small letters or with a space', fix: { call: call.toUpperCase().replace(/\s+/g, '') } });
        else if (!callOk(call)) out.push({ k: 'call', q, msg: 'does not look like a call sign' });
      }
      if (C.time && !(+q.t > 0)) out.push({ k: 'time', q, msg: 'no date / time' });
      if (C.band && !q.band) { const b = q.khz > 100 ? bandOf(q.khz) : ''; out.push(b ? { k: 'band', q, msg: 'no band (the frequency says ' + b + ')', fix: { band: b } } : { k: 'band', q, msg: 'no band or frequency' }); }
      if (C.mode && !q.mode) out.push({ k: 'mode', q, msg: 'no mode' });
      if (C.station) {
        if (!q.station && me && AP.stdCall(me)) out.push({ k: 'station', q, msg: 'no station call (will be ' + me + ')', fix: { station: me } });
        else if (q.station && !AP.stdCall(String(q.station).split('/').sort((a, b) => b.length - a.length)[0])) out.push({ k: 'station', q, msg: 'station call ' + q.station + ' is not a real call' });
      }
      if (C.park) [...(q.myrefs || []), ...(q.refs || [])].forEach(r => { if (!parkOk(String(r))) out.push({ k: 'park', q, msg: 'park number ' + r + ' does not look right' }); });
      if (C.dupe && +q.t > 0) {
        const key = [String(call).toUpperCase(), q.band || bandOf(q.khz), L.adMode ? L.adMode(q.mode)[0] : q.mode, day(q.t), (q.myrefs || []).join('+'), stCall(q)].join('|');
        if (seen[key]) out.push({ k: 'dupe', q, msg: 'same call, band and mode as ' + new Date(seen[key].t).toISOString().slice(11, 16) + ' UTC (POTA counts it once)' }); else seen[key] = q;
      }
    }
    return out;
  }
  /* activations: park + station call + UTC day → contacts POTA counts (no doubles) */
  function acts(Q) {
    const A = {};
    for (const q of Q) {
      if (!(+q.t > 0)) continue;
      for (const p of (q.myrefs || []).filter(isPota)) {
        const k = p + '|' + stCall(q) + '|' + day(q.t), a = A[k] || (A[k] = { park: p, call: stCall(q), day: day(q.t), n: 0, seen: new Set() });
        const d = [String(q.call || '').toUpperCase(), q.band || bandOf(q.khz), L.adMode ? L.adMode(q.mode)[0] : q.mode].join('|');
        if (!a.seen.has(d)) { a.seen.add(d); a.n++; }
      }
    }
    return Object.values(A).sort((a, b) => a.day < b.day ? -1 : a.day > b.day ? 1 : a.park < b.park ? -1 : 1);
  }
  function stats(Q) {
    const by = {}; let best = 0, bestAt = 0; const ts = Q.map(q => +q.t).filter(t => t > 0).sort((a, b) => a - b);
    Q.forEach(q => { const k = (q.band || bandOf(q.khz) || '?') + ' ' + (q.mode || '?'); by[k] = (by[k] || 0) + 1; });
    for (let i = 0, j = 0; i < ts.length; i++) { while (ts[i] - ts[j] > 3600000) j++; if (i - j + 1 > best) { best = i - j + 1; bestAt = ts[j]; } }
    return { by: Object.entries(by).sort((a, b) => b[1] - a[1]), best, bestAt };
  }
  /* ---------- POTA files ---------- */
  const clean = s => String(s || '').replace(/[^A-Z0-9-]/gi, '');
  function files(Q) {
    const groups = {}, pota = Q.filter(q => (q.myrefs || []).some(isPota));
    if (C.split === 'one') return [{ name: nameOf(meCall(), (pota[0] && pota[0].myrefs.find(isPota)) || '', Q[0] ? day(Q[0].t) : day(Date.now()), Q), list: Q, park: '' }];
    for (const q of pota) for (const p of q.myrefs.filter(isPota)) {
      const k = p + '|' + stCall(q) + (C.split === 'day' ? '|' + day(q.t) : ''), g = groups[k] || (groups[k] = { park: p, call: stCall(q), list: [] });
      g.list.push(q);
    }
    return Object.values(groups).map(g => ({ name: nameOf(g.call, g.park, day(g.list[0].t), g.list), list: g.list, park: g.park, call: g.call }));
  }
  function nameOf(call, park, d, Q) {
    const st = (() => { const s = (Q.find(q => q.mc) || {}).mc || AP.S.st || ''; return String(s).split(',')[0].trim().toUpperCase(); })();
    return C.name === 'pota' ? clean(call.replace(/\//g, '_')) + '@' + clean(park || 'LOG') + '-' + d.replace(/-/g, '') + '.adi'
      : [clean(call.replace(/\//g, '_')), clean(park), d, /^[A-Z]{2}$/.test(st) ? st : ''].filter(Boolean).join(' ') + '.adi';
  }
  function save() {
    const Q = list(); if (!Q.length) { AP.toast('Nothing in this log yet.', 3000, 'bad'); return []; }
    const F = files(Q);
    if (!F.length) { AP.toast('No contacts with one of your POTA parks: pick EVERYTHING IN ONE FILE, or set the park on the contacts.', 5000, 'bad'); return []; }
    F.forEach((f, i) => setTimeout(() => AP.saveFile(L.adif(f.list, f.park || undefined), f.name, 'text/plain'), i * 400));
    AP.toast('⬇ Saved ' + F.length + ' file' + (F.length > 1 ? 's' : '') + ': ' + esc(F.map(f => f.name).join(', ')), 6000, 'log');
    return F.map(f => f.name);
  }
  function fixAll() {
    const fx = check(list()).filter(x => x.fix); let n = 0;
    fx.forEach(x => { if (L.edit(x.q.id, x.fix)) n++; });
    return n;
  }
  /* ---------- the sheet ---------- */
  function sheet() {
    const Q = list(), P = check(Q), A = acts(Q), S = stats(Q), nFix = P.filter(x => x.fix).length;
    const when = q => +q.t > 0 ? new Date(q.t).toISOString().slice(5, 16).replace('T', ' ') : '?';
    const prob = P.length ? `<ul class="hint" style="margin:4px 0 8px 18px;padding:0">${P.slice(0, 40).map(x => `<li><b>${esc(x.q.call || '?')}</b> ${esc(when(x.q))} · ${esc(x.msg)}${x.fix ? ' <span style="color:var(--ok,#5c5)">(FIX ALL fixes it)</span>' : ''}</li>`).join('')}${P.length > 40 ? `<li>…and ${P.length - 40} more</li>` : ''}</ul>`
      : '<p style="color:var(--ok,#5c5)">✅ No problems found.</p>';
    const act = !C.ten ? '' : A.length ? `<h3 class="sh">Activations (park · call · UTC day)</h3><ul class="hint" style="margin:4px 0 8px 18px;padding:0">${A.map(a => `<li>${esc(a.park)} · ${esc(a.call)} · ${esc(a.day)} · <b>${a.n}</b> ${a.n >= 10 ? '✅ valid' : '— ' + (10 - a.n) + ' more for a valid activation'}</li>`).join('')}</ul>` : '<p class="hint">No contacts from one of your POTA parks in this log (hunting is fine: nothing to count).</p>';
    AP.sheet('✅ Check & save for POTA', `
      <p><b>${Q.length}</b> contact${Q.length === 1 ? '' : 's'} in this log · ${P.length ? '<b style="color:var(--bad)">' + P.length + ' to look at</b>' : 'all good'}</p>
      ${prob}${act}
      <details><summary class="hint">What to check (${CHECKS.filter(c => C[c[0]]).length} of ${CHECKS.length})</summary>${CHECKS.map(c => `<label class="ck" style="display:flex;margin:4px 0"><input type="checkbox" data-chk="${c[0]}"${C[c[0]] ? ' checked' : ''}> <span>${esc(c[1])}</span></label>`).join('')}</details>
      <div class="grid2"><label class="e">FILES<select id="ckSplit"><option value="park"${C.split === 'park' ? ' selected' : ''}>one per park + call (POTA)</option><option value="day"${C.split === 'day' ? ' selected' : ''}>one per park + call + UTC day</option><option value="one"${C.split === 'one' ? ' selected' : ''}>everything in one file</option></select></label>
        <label class="e">FILE NAMES<select id="ckName"><option value="pota"${C.name === 'pota' ? ' selected' : ''}>CALL@PARK-DATE (POTA)</option><option value="words"${C.name === 'words' ? ' selected' : ''}>CALL PARK DATE STATE</option></select></label></div>
      <p class="hint" id="ckFiles">${esc(files(Q).map(f => f.name + ' (' + f.list.length + ')').join(' · ') || 'no POTA files to make')}</p>
      <div class="row">${nFix ? `<button type="button" class="b" id="ckFix">🔧 FIX ALL (${nFix})</button>` : ''}<button type="button" class="b gold" id="ckSave">⬇ SAVE FOR POTA</button>
        <button type="button" class="b" id="ckUp">⬆ POTA UPLOAD PAGE ›</button><button type="button" class="b" id="ckSite">🌐 OPEN THE WEBSITE CHECKER ›</button></div>
      <h3 class="sh">Rates</h3><p class="hint">Best 60 minutes: <b>${S.best}</b>${S.best ? ' from ' + esc(new Date(S.bestAt).toISOString().slice(11, 16)) + ' UTC' : ''} · ${S.by.slice(0, 8).map(([k, n]) => esc(k) + ' <b>' + n + '</b>').join(' · ') || 'no contacts'}</p>
      <p class="hint">POTA wants one file per park (and per call when you change calls). Upload at pota.app → your call → Log Uploads. The website checker has the full editor (columns, find &amp; replace): open the saved file there. Everything stays on this device.</p>`);
    document.querySelectorAll('[data-chk]').forEach(b => { b.onchange = () => { C[b.dataset.chk] = b.checked; cSave(); AP.shut(); sheet(); }; });
    $('ckSplit').onchange = () => { C.split = $('ckSplit').value; cSave(); $('ckFiles').textContent = files(list()).map(f => f.name + ' (' + f.list.length + ')').join(' · ') || 'no POTA files to make'; };
    $('ckName').onchange = () => { C.name = $('ckName').value; cSave(); $('ckFiles').textContent = files(list()).map(f => f.name + ' (' + f.list.length + ')').join(' · ') || 'no POTA files to make'; };
    if ($('ckFix')) $('ckFix').onclick = () => { const n = fixAll(); AP.shut(); AP.toast('🔧 Fixed ' + n + ' contact' + (n === 1 ? '' : 's') + '.', 3000, 'log'); sheet(); };
    $('ckSave').onclick = () => save();
    $('ckUp').onclick = () => G.open(UPLOAD, '_blank');
    $('ckSite').onclick = () => G.open(SITE, '_blank');
  }
  /* the ✅ CHECK chip on the LOG strip + the STATION → Log files button */
  const strip = $('lgStrip');
  if (strip && !$('lgCheck')) { (($('lgAdd') && $('lgAdd').insertAdjacentHTML.bind($('lgAdd'), 'beforebegin')) || strip.insertAdjacentHTML.bind(strip, 'beforeend'))('<button type="button" class="chip set" id="lgCheck" title="Check this log and save it for POTA / QRZ">✅ CHECK</button>'); $('lgCheck').onclick = sheet; }
  if ($('stCheck')) $('stCheck').onclick = sheet;
  G.KPCLogCheck = { sheet, check, acts, stats, files, save, fixAll, _c: C };
})(window);
