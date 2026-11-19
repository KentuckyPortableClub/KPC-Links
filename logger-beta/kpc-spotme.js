/* KPC app: SPOT ME + RE-SPOT by hand + AUTO SPOT ME for activators (Nov 17) (Opus, Oct 25; Brandon: 'go ahead with the spotting for the 3 programs and respotting pota stations').
   POTA: api.pota.app/spot/ takes a spot from any program, no sign-in (what pota.app's own page, HAMRS and PoLo use):
     POST JSON {activator, spotter, frequency (kHz), reference, mode, source, comments}.
   SOTA: SOTAwatch only takes spots from a signed-in SOTA account (no open door for apps): the button opens SOTAwatch's spot page.
   WWFF: Spotline gives programs an API key on request (OH3CUF, spots.wwff.co/info): until KPC has one the button opens Spotline.
   QRM CHECK (the website's rule, kpc-links kpc-qrm.js): before a spot goes out, look for another activator spotted in the last 20 min
   close by — SSB ±3 kHz, AM ±6, FM ±10, CW / RTTY ±1, PSK ±0.5; FT8 / FT4 / FT2 / JS8 never warn (everyone shares the same spot).
   A practice call (K4TEST) never spots. Opened from the CALL box (SPOTME / QRV / QSY / QRT), the 📣 chip on the LOG screen, or a spot's sheet. */
(function (G) {
  'use strict';
  const AP = G.KPCApp, $ = id => document.getElementById(id), esc = AP && AP.esc;
  if (!AP) return;
  const QRMK = { SSB: 3, USB: 3, LSB: 3, AM: 6, FM: 10, CW: 1, RTTY: 1, PSK31: 0.5, PSK63: 0.5, PSK: 0.5 };
  const noQrm = m => /^(FT8|FT4|FT2|JS8|WSPR|FST4|Q65)$/.test(m);
  const sigOf = r => /^[A-Z0-9]*FF-/.test(r) ? 'WWFF' : /^[A-Z0-9]+\/[A-Z]{2}-\d{3}$/.test(r) ? 'SOTA' : 'POTA';
  const modeOut = m => { m = String(m || '').toUpperCase(); return /^(USB|LSB|SSB|PHONE)$/.test(m) ? 'SSB' : /^(PSK31|PSK63|PSK125)$/.test(m) ? 'PSK31' : m; };
  function where() {
    const L = G.KPCLog, d = L ? L.dock : { khz: 14074, mode: 'FT8' }, md = G.KPCModes && KPCModes.active(), dm = String(d.mode || '').toUpperCase();
    /* FT8 / the digital screens: their own dial (+ my TX audio for FT8 the way POTA lists it: the dial) */
    if (md && /^(FT8|FT4|CW|RTTY|PSK31|SSTV)$/.test(md.id) && document.body.dataset.screen === 'digi') return { khz: md.khz(), mode: md.id === 'PSK31' ? 'PSK31' : md.id };
    return { khz: +d.khz || 0, mode: dm };
  }
  function qrmNear(khz, mode, me) {
    if (noQrm(mode) || !G.KPCSpots) return [];
    const w = QRMK[mode] || 3, cut = Date.now() - 20 * 60000;
    return KPCSpots.all().filter(s => s.t >= cut && s.call !== me && s.refs && s.refs.length && Math.abs(s.khz - khz) <= w && !noQrm(String(s.mode || '').toUpperCase()));
  }
  async function postPota(o) {
    const body = JSON.stringify({ activator: o.activator, spotter: o.spotter, frequency: String(Math.round(o.khz * 10) / 10), reference: o.ref, mode: o.mode, source: 'KPC app', comments: o.comment || '' });
    const r = await AP.net.raw('https://api.pota.app/spot/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body, ms: 12000 });
    if (!r || !r.ok) throw new Error((r && (r.err || ('POTA answered ' + r.status))) || 'no answer');
    return true;
  }
  function sheet(word, re) {
    const me = AP.myCall(), w = where();
    const refs = re ? (re.refs || []) : (G.KPCLog ? KPCLog.refList(AP.S.ref || '') : []);
    const act = re ? re.call : me, khz = re ? re.khz : w.khz, mode = modeOut(re ? re.mode : w.mode);
    const progs = [...new Set(refs.map(sigOf))];
    const bad = !me ? 'Put your call sign in STATION → My station first.' : !AP.stdCall(me) ? 'Spotting needs your real call sign (a practice call like K4TEST must never be spotted).' : !refs.length ? (re ? 'That spot has no park number.' : 'Put your park number in first (the 🌲 MY PARK chip on the LOG screen).') : !(khz > 100) ? 'No frequency yet: set the band / frequency on the LOG screen chip.' : '';
    const near = bad || re ? [] : qrmNear(khz, mode, me);
    const dflt = re ? 'TU' : word === 'QRT' ? 'QRT, thanks all' : word === 'QSY' ? 'QSY' : word === 'QRV' ? 'QRV' : '';
    AP.sheet(re ? '📣 Re-spot ' + esc(act) : '📣 Spot me', `
      ${bad ? `<p class="bad">${esc(bad)}</p>` : `<p><b>${esc(act)}</b> · ${esc((khz / 1000).toFixed(3))} MHz ${esc(mode)} · ${esc(refs.join(' + '))}</p>`}
      ${near.length ? `<p class="bad">⚠ Someone else is close: ${near.slice(0, 3).map(s => `<b>${esc(s.call)}</b> ${esc((s.khz / 1000).toFixed(3))} ${esc(s.mode || '')} (${esc(s.refs.join('+'))}, ${Math.round((Date.now() - s.t) / 60000)} min ago)`).join(' · ')}. Move a little before you spot, or spot anyway.</p>` : ''}
      <div class="grid2"><label class="e">FREQUENCY (kHz)<input id="smKhz" inputmode="decimal" value="${esc(String(khz || ''))}"></label><label class="e">MODE<input id="smMode" autocapitalize="characters" value="${esc(mode)}"></label></div>
      <label class="e wide">COMMENT<input id="smCom" maxlength="60" value="${esc(dflt)}" placeholder="optional: QRV, QRT, 2-fer…"></label>
      <div class="row">${progs.includes('POTA') || !progs.length ? `<button type="button" class="b gold" id="smPota"${bad ? ' disabled' : ''}>📣 SPOT ON POTA</button>` : ''}
        ${progs.includes('SOTA') ? '<button type="button" class="b" id="smSota">⛰ SOTAWATCH ›</button>' : ''}${progs.includes('WWFF') ? '<button type="button" class="b" id="smWwff">🌳 WWFF SPOTLINE ›</button>' : ''}</div>
      <p class="hint">POTA spots go straight in. SOTAwatch takes spots only from a signed-in SOTA account and WWFF only from programs with a Spotline key, so those two buttons open their spot page in the browser for now.${re ? ' A re-spot tells the hunters this station is still on the air there.' : ''}</p>`);
    const go = async () => {
      const k = parseFloat($('smKhz').value), m = modeOut($('smMode').value), com = $('smCom').value.trim();
      const pr = refs.filter(r => sigOf(r) === 'POTA'); if (!pr.length) { AP.toast('No POTA park number to spot.', 3000, 'bad'); return; }
      if (!AP.net.online()) { AP.toast('No signal right now: the spot did not go out.', 4000, 'bad'); return; }
      $('smPota').disabled = true; $('smPota').textContent = 'Sending…';
      try { for (const ref of pr) await postPota({ activator: act, spotter: me, khz: k, ref, mode: m, comment: com }); AP.shut(); AP.toast('📣 Spotted on POTA: ' + esc(act) + ' ' + (k / 1000).toFixed(3) + ' ' + esc(m) + ' ' + esc(pr.join(' + ')), 4000, 'log'); LAST = { t: Date.now(), khz: k };
        if (G.KPCSpots && KPCSpots.feed) KPCSpots.feed('own', [{ call: act, khz: k, mode: m, refs: pr, comment: com, spotter: me, t: Date.now() }]); }
      catch (e) { $('smPota').disabled = false; $('smPota').textContent = '📣 SPOT ON POTA'; AP.toast('The spot did not go: ' + esc(e.message || e), 5000, 'bad'); }
    };
    if ($('smPota')) $('smPota').onclick = go;
    if ($('smSota')) $('smSota').onclick = () => G.open('https://sotawatch.sota.org.uk/en/', '_blank');
    if ($('smWwff')) $('smWwff').onclick = () => G.open('https://spots.wwff.co/', '_blank');
  }
  let LAST = null;
  /* the 📣 chip on the LOG dock (activating only) */
  const chips = $('lgDock') && $('lgDock').querySelector('.chips');
  if (chips && !$('dkSpot')) { const p = $('dkP2p'); (p || chips.lastElementChild).insertAdjacentHTML('beforebegin', '<button type="button" class="chip" id="dkSpot" title="Spot me on POTA (QRM check first)">📣 SPOT ME</button>'); $('dkSpot').onclick = () => sheet(''); }
  /* Nov 17: no park number = no 📣 SPOT ME chip (spotting is for activators) */
  const showChip = () => { const c = $('dkSpot'); if (c) c.hidden = AP.me().hunt || !String(AP.S.ref || '').trim(); };
  AP.on('me', showChip); AP.on('log', showChip); setInterval(showChip, 5000); showChip();
  /* Nov 17 (Brandon: 'Hunters side remove it not needed'): the hunter AUTO RE-SPOT (Oct 30) is gone, with its STATION
     button and its kpcAppRespot setting. A hunter can still re-spot by hand (📣 RE-SPOT on a spot's sheet). */
  try { localStorage.removeItem('kpcAppRespot'); } catch (e) {}

  /* ---------------- AUTO SPOT ME for the ACTIVATOR (to-do 2; Brandon Nov 11 + Nov 17) ----------------
     After my FIRST logged contact at a park, and again on a new band, mode or frequency (QSY), the app OFFERS once to spot
     me: it shows exactly what will go to POTA and waits for YES. Never after every contact, never on its own the first time.
     Only with a POTA park number set (Nov 17: 'remove the spot if they dont have a pota park number in'); with a WWFF or
     SOTA reference it offers the 🌳 Spotline / ⛰ SOTAwatch page instead (neither lets an app post), details shown to copy.
     KEEP ME SPOTTED (OFF / 10 / 15 / 20 min): after a YES, the app spots me again on that timer, only while I am still
     logging contacts on that same frequency and mode; it stops when I go quiet (no contact in that many minutes) and stops
     on a QSY (the next contact there asks afresh). Limits on what the app sends by itself: 1 spot per 5 minutes, 4 an hour.
     DON'T ASK AGAIN THIS ACTIVATION = quiet until the park or the UTC day changes. A practice call never spots. */
  const AS = Object.assign({ ask: true, keep: 0 }, (() => { try { return JSON.parse(localStorage.getItem('kpcAppAutoSpot') || '{}'); } catch (e) { return {}; } })());
  const asSave = () => { try { localStorage.setItem('kpcAppAutoSpot', JSON.stringify(AS)); } catch (e) {} asBtn(); };
  const tolOf = m => /^(SSB|AM|FM)$/.test(m) ? 2 : 1;   /* kHz: further than this from the last spot = a QSY */
  const myRefsAll = () => [...new Set(String(AP.S.ref || '').toUpperCase().split(/[\s,;+]+/).map(x => x.trim()).filter(x => /^[A-Z0-9]+(\/[A-Z]{2})?-[A-Z0-9]+$/.test(x)))];
  const potaRefs = () => myRefsAll().filter(r => sigOf(r) === 'POTA' && /^[A-Z0-9]{1,3}-\d{4,5}$/.test(r));
  const utcDay = () => new Date(AP.now ? AP.now() : Date.now()).toISOString().slice(0, 10);
  const actKey = () => myRefsAll().join('+') + '|' + utcDay();
  const SENT = [];          /* times the app spotted me by itself (offer YES or keep-me-spotted) */
  let ON = null;            /* what was last offered / spotted: {act, khz, mode, at (last spot), yes, lastQ} */
  let QUIET = '';           /* actKey() of 'don't ask again this activation' */
  const room = () => { const t = Date.now(); while (SENT.length && t - SENT[0] > 3600000) SENT.shift(); return !(SENT.length && t - SENT[SENT.length - 1] < 300000) && SENT.length < 4; };
  async function spotNow(khz, mode, com, why) {
    const me = AP.myCall(), pr = potaRefs();
    if (!me || !AP.stdCall(me) || !pr.length || !(khz > 100)) return false;
    if (!room()) { if (why !== 'keep') AP.toast('Not spotted: the app keeps to 1 spot every 5 minutes and 4 an hour. 📣 SPOT ME by hand still works.', 4500, 'bad'); return false; }
    if (!AP.net.online()) { AP.toast('No signal right now: the spot did not go out.', 4000, 'bad'); return false; }
    SENT.push(Date.now());
    try {
      for (const ref of pr) await API._post({ activator: me, spotter: me, khz, ref, mode, comment: com || '' });
      LAST = { t: Date.now(), khz, auto: why };
      if (ON) ON.at = Date.now();
      AP.toast('📣 ' + (why === 'keep' ? 'Kept you spotted' : 'Spotted') + ' on POTA: ' + esc(me) + ' ' + (khz / 1000).toFixed(3) + ' ' + esc(mode) + ' ' + esc(pr.join(' + ')), 3500, 'log');
      if (G.KPCSpots && KPCSpots.feed) KPCSpots.feed('own', [{ call: me, khz, mode, refs: pr, comment: com || '', spotter: me, t: Date.now() }]);
      return true;
    } catch (e) { SENT.pop(); AP.toast('The spot did not go: ' + esc(e.message || e), 5000, 'bad'); return false; }
  }
  function offer(khz, mode) {
    const me = AP.myCall(), pr = potaRefs(), other = myRefsAll().filter(r => sigOf(r) !== 'POTA'), progs = [...new Set(other.map(sigOf))];
    ON = { act: actKey(), khz, mode, at: 0, yes: false, lastQ: Date.now() };
    if (!pr.length && !other.length) return;
    const near = pr.length ? qrmNear(khz, mode, me) : [];
    AP.sheet('📣 Spot me?', `
      <p><b>${esc(me)}</b> · ${esc((khz / 1000).toFixed(3))} MHz ${esc(mode)} · ${esc(myRefsAll().join(' + '))}</p>
      ${near.length ? `<p class="bad">⚠ Someone else is close: ${near.slice(0, 3).map(x => `<b>${esc(x.call)}</b> ${esc((x.khz / 1000).toFixed(3))} ${esc(x.mode || '')}`).join(' · ')}.</p>` : ''}
      ${pr.length ? `<label class="e wide">COMMENT<input id="asCom" maxlength="60" value="" placeholder="optional: QRV, 2-fer…"></label>
      <label class="e wide">KEEP ME SPOTTED<select id="asKeep">${[0, 10, 15, 20].map(m => `<option value="${m}"${+AS.keep === m ? ' selected' : ''}>${m ? 'every ' + m + ' min while I keep logging here' : 'OFF (just this once)'}</option>`).join('')}</select></label>` : ''}
      <div class="row">${pr.length ? '<button type="button" class="b gold" id="asYes">📣 YES, SPOT ME ON POTA</button>' : ''}
        ${progs.includes('WWFF') ? '<button type="button" class="b" id="asWwff">🌳 WWFF SPOTLINE ›</button>' : ''}${progs.includes('SOTA') ? '<button type="button" class="b" id="asSota">⛰ SOTAWATCH ›</button>' : ''}
        <button type="button" class="b" id="asNo">NOT NOW</button><button type="button" class="b" id="asQuiet">DON'T ASK AGAIN THIS ACTIVATION</button></div>
      <p class="hint">${pr.length ? 'Nothing goes to POTA until you press YES. ' : ''}${progs.length ? 'WWFF and SOTA do not take spots from apps, so their button opens the spot page: type the frequency and mode shown above. ' : ''}The app asks again only on a new band, mode or frequency. Turn this off in STATION → Log files → 📣 AUTO SPOT ME.</p>`);
    if ($('asYes')) $('asYes').onclick = async () => { AS.keep = +$('asKeep').value || 0; asSave(); const com = $('asCom').value.trim(); ON.com = com; AP.shut(); ON.yes = await spotNow(khz, mode, com, 'offer'); };
    if ($('asWwff')) $('asWwff').onclick = () => G.open('https://spots.wwff.co/', '_blank');
    if ($('asSota')) $('asSota').onclick = () => G.open('https://sotawatch.sota.org.uk/en/', '_blank');
    $('asNo').onclick = () => AP.shut();
    $('asQuiet').onclick = () => { QUIET = actKey(); AP.shut(); AP.toast('OK: no more spot offers at this park today.', 3000); };
  }
  function onLog(q) {
    if (!AS.ask || !q || q.d || AP.me().hunt) return;
    if (Date.now() - (+q.t || Date.now()) > 15 * 60000) return;   /* an earlier contact typed in later */
    const me = AP.myCall(); if (!me || !AP.stdCall(me) || !myRefsAll().length || QUIET === actKey()) return;
    const khz = +q.khz || where().khz, mode = modeOut(q.mode || where().mode); if (!(khz > 100)) return;
    const same = ON && ON.act === actKey() && ON.mode === mode && Math.abs(ON.khz - khz) <= tolOf(mode);
    if (same) { ON.lastQ = Date.now(); return; }
    if (LAST && Date.now() - LAST.t < 300000 && Math.abs(LAST.khz - khz) <= tolOf(mode)) { ON = { act: actKey(), khz, mode, at: LAST.t, yes: true, lastQ: Date.now() }; return; }   /* spotted by hand just now */
    if (!$('sheet').hidden) return;   /* another sheet is up: ask on the next contact */
    offer(khz, mode);
  }
  AP.on('log', e => { if (e && e.why === 'add') { const q = (e.recs || []).slice(-1)[0]; if (q) setTimeout(() => onLog(q), 600); } });
  function keepTick() {
    if (!ON || !ON.yes || !(+AS.keep) || AP.me().hunt || ON.act !== actKey() || !potaRefs().length) return;
    const k = +AS.keep * 60000, now = Date.now(), w = where();
    if (now - ON.lastQ > k) return;                                                      /* gone quiet: stop */
    if (w.khz > 100 && (Math.abs(w.khz - ON.khz) > tolOf(ON.mode) || (w.mode && modeOut(w.mode) !== ON.mode))) return;   /* QSY: stop */
    if (now - ON.at < k) return;
    spotNow(ON.khz, ON.mode, ON.com || '', 'keep');
  }
  setInterval(keepTick, 30000);
  function asBtn() { const b = $('stAutoSpot'); if (b) b.textContent = '📣 AUTO SPOT ME: ' + (!AS.ask ? 'OFF' : 'ASK' + (+AS.keep ? ' · KEEP ' + AS.keep + ' MIN' : '')); }
  function asSheet() {
    AP.sheet('📣 Auto spot me (activating)', `<p class="hint">When you <b>activate</b> a park, the app offers to spot you after your first contact, and again when you change band, mode or frequency. Nothing goes out until you press YES. It needs a POTA park number; with a WWFF or SOTA reference it opens their spot page instead.</p>
      <label class="ck"><input type="checkbox" id="asAsk"${AS.ask ? ' checked' : ''}> Offer to spot me</label>
      <label class="e wide">KEEP ME SPOTTED<select id="asKeep2">${[0, 10, 15, 20].map(m => `<option value="${m}"${+AS.keep === m ? ' selected' : ''}>${m ? 'every ' + m + ' min' : 'OFF'}</option>`).join('')}</select></label>
      <p class="hint">Keep me spotted re-spots you only while you are still logging contacts on the same frequency; it stops when you go quiet or QSY. The app sends at most 1 spot every 5 minutes and 4 an hour by itself. Never with a practice call.</p>`);
    $('asAsk').onchange = () => { AS.ask = $('asAsk').checked; asSave(); };
    $('asKeep2').onchange = () => { AS.keep = +$('asKeep2').value || 0; asSave(); };
  }
  if ($('stAutoSpot')) { $('stAutoSpot').onclick = asSheet; asBtn(); }
  const API = G.KPCSpotMe = { sheet: w => sheet(w), respot: s => sheet('', s), qrmNear, last: () => LAST, _post: postPota, autoSheet: asSheet, _as: AS, _on: () => ON, _sent: SENT, _tick: keepTick, _onLog: onLog, _reset: () => { ON = null; QUIET = ''; SENT.length = 0; LAST = null; } };
})(window);
