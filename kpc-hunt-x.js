/* KPC Hunters Lounge + VIP Lounge: logger extras (Nov 10 2026, Opus; decided_by: KPC owner, 2026-11-10).
   Only ADDS to the lounges (nothing moved or taken away). Loaded after kpc-hunt.js on kpc-hunters.html, kpc-hunt.html and the beta rooms.
   - 📜 MY LICENCE CLASS + IN MY CLASS ONLY in ⚙ FILTERS (the US band plan by class, the KPC app's AP.bandPlan). Remembered (kpcHuntCls).
   - ▶ SCAN in the spots bar: steps through the spots shown (voice + CW; FT8 / FT4 skipped) every few seconds. With a CAT radio it tunes each
     one (the dock fills in); with none it highlights + scrolls to each. A second press, typing a call, or Esc stops it. (kpcHuntScan)
   - ⚙ on the logging dock: ONE small floating radio window (drag it by its top bar) with tabs 📻 Radio · 📊 Meters · 📍 Bands / Tune / SWR ·
     🎧 Audio / Mic · 🎛 More · 📟 CW. It borrows kpc-lounge-radio.js's box (the public lounge's RADIO CONTROL card gets it back when the
     window closes). Remembers the last tab + where it was (kpcHuntPop). Works with no radio (each part says to connect first).
   - 🎧 AUDIO / MIC: hear the radio here (with kpc-nr.js's clean-up), and 🎙 HOLD TO TALK from this computer's mic through NATURAL /
     PUNCH / CONTEST (the KPC app's voice shaper), MIC LEVEL, the radio's MIC GAIN and RF POWER over CAT where the radio takes them.
   - 📟 CW: a memory keyer (6 memories you can edit, {CALL} = the call in the dock, {MY} = your call) + free text; the radio's own keyer
     sends it over CAT (Icom, Kenwood / Elecraft / QRP Labs, the newer Yaesu: kpc-cat.js cw()). Hidden without a CAT radio; greyed on radios
     that can't take typed CW. The dock gets a 📟 button while a radio that can is connected. */
(function (G) {
  'use strict';
  const $ = id => document.getElementById(id);
  if (!$('dkForm') || G.KPCHuntX) return;
  const K = () => G.KPCCat, LR = () => G.KPCLoungeRx;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const conn = () => !!(K() && K().connected());
  let msgT = 0;
  function note(t, bad) { let m = $('hxMsg'); if (!m) { m = document.createElement('div'); m.id = 'hxMsg'; document.body.appendChild(m); } m.textContent = t; m.className = bad ? 'bad' : ''; m.hidden = false; clearTimeout(msgT); msgT = setTimeout(() => { m.hidden = true; }, bad ? 5000 : 2600); }

  /* ================================================================ 📜 LICENCE CLASS (the US plan, from the KPC app's kpc-app.js bandPlan) */
  const PLAN = [
    [1800, 2000, 'GAE', 'all'],
    [3500, 3525, 'E', 'cw'], [3525, 3600, 'GAE', 'cw'], [3525, 3600, 'T', 'cwo'], [3600, 3700, 'AE', 'ph'], [3700, 3800, 'AE', 'ph'], [3800, 4000, 'GAE', 'ph'],
    [5330.5, 5406.4, 'GAE', 'all'],
    [7000, 7025, 'E', 'cw'], [7025, 7125, 'GAE', 'cw'], [7025, 7125, 'T', 'cwo'], [7125, 7175, 'AE', 'ph'], [7175, 7300, 'GAE', 'ph'],
    [10100, 10150, 'GAE', 'cw'],
    [14000, 14025, 'E', 'cw'], [14025, 14150, 'GAE', 'cw'], [14150, 14175, 'E', 'ph'], [14175, 14225, 'AE', 'ph'], [14225, 14350, 'GAE', 'ph'],
    [18068, 18110, 'GAE', 'cw'], [18110, 18168, 'GAE', 'ph'],
    [21000, 21025, 'E', 'cw'], [21025, 21200, 'GAE', 'cw'], [21025, 21200, 'T', 'cwo'], [21200, 21225, 'E', 'ph'], [21225, 21275, 'AE', 'ph'], [21275, 21450, 'GAE', 'ph'],
    [24890, 24930, 'GAE', 'cw'], [24930, 24990, 'GAE', 'ph'],
    [28000, 28300, 'TGAE', 'cw'], [28300, 28500, 'TGAE', 'ph'], [28500, 29700, 'GAE', 'ph'],
    [50000, 54000, 'TGAE', 'all'], [144000, 148000, 'TGAE', 'all'], [222000, 225000, 'TGAE', 'all'], [420000, 450000, 'TGAE', 'all'], [902000, 928000, 'TGAE', 'all'], [1240000, 1300000, 'TGAE', 'all']
  ];
  const isCwData = m => /CW|FT|RTTY|PSK|HELL|WSPR|JS8|APRS|PKT|DATA|MFSK|OLIVIA/i.test(m || '') && !/SSB|USB|LSB|FM|AM|SSTV/i.test(m || '');
  function allowed(khz, cls, mode) {
    cls = String(cls || 'E').toUpperCase()[0]; if (!'TGAE'.includes(cls)) cls = 'E';
    return PLAN.some(s => khz >= s[0] && khz <= s[1] && s[2].includes(cls) && (!mode || s[3] === 'all' || (s[3] === 'cwo' ? /CW/i.test(mode) : s[3] === 'cw' ? isCwData(mode) || /CW/i.test(mode) : !isCwData(mode))));
  }
  const CL = Object.assign({ cls: '', on: false }, LS('kpcHuntCls', {}));
  const CLN = { T: 'TECH', G: 'GENERAL', A: 'ADVANCED', E: 'EXTRA' };
  /* a spot outside the US bands (DX on a non-US plan, VHF repeaters…) is judged by frequency + mode only; unknown frequency = shown */
  function pass(s) { if (!CL.on || !CL.cls || !s || !(+s.khz > 0)) return true; return allowed(+s.khz, CL.cls, s.mode || ''); }
  function clsChips() {
    const g = $('hxCls'); if (!g) return;
    g.innerHTML = '<span>MY CLASS</span>' + Object.keys(CLN).map(c => `<button type="button" class="hl-chip" data-hxcls="${c}" aria-pressed="${CL.cls === c}">${CLN[c]}</button>`).join('') +
      `<button type="button" class="hl-chip" id="hxClsOn" aria-pressed="${!!CL.on}"${CL.cls ? '' : ' disabled title="Pick your class first"'}>📜 IN MY CLASS ONLY</button>`;
  }
  function clsMount() {
    const only = document.querySelector('#hlFilters [aria-label="Only"]'); if (!only || $('hxCls')) return;
    only.insertAdjacentHTML('afterend', '<div class="hw-g" id="hxCls" role="group" aria-label="My licence class"></div>');
    clsChips();
    $('hxCls').addEventListener('click', e => {
      const c = e.target.closest('[data-hxcls]');
      if (c) { const v = c.dataset.hxcls; CL.cls = CL.cls === v ? '' : v; if (CL.cls && !CL.on) CL.on = true; if (!CL.cls) CL.on = false; }
      else if (e.target.closest('#hxClsOn')) { if (!CL.cls) return; CL.on = !CL.on; } else return;
      SV('kpcHuntCls', CL); clsChips(); redraw();
      note(CL.on ? '📜 Only spots your ' + CLN[CL.cls] + ' licence can work.' : '📜 Showing every spot (class filter off).');
    });
  }
  const redraw = () => { try { G.KPCHunt && KPCHunt.draw && KPCHunt.draw(); } catch (e) {} };

  /* ================================================================ ▶ SCAN */
  const SC = Object.assign({ sec: 10 }, LS('kpcHuntScan', {}));
  let scT = 0, scI = -1, scK = '';
  function scMount() {
    /* lives on the list bar (next to CARDS / TABLE), not the tab row: the tab row is full at laptop width and on a phone it is hidden */
    const bar = document.querySelector('.hl-viewbar'); if (!bar || $('hxScan')) return;
    const at = bar.querySelector('.hl-vt');
    const h = `<span class="hx-scg" role="group" aria-label="Scan"><button type="button" class="hl-chip hx-scan" id="hxScan" title="Step the radio through the spots shown (voice + CW). Tap again to stop.">▶ SCAN</button><select class="hx-scs" id="hxScS" aria-label="Seconds on each spot" title="Seconds on each spot">${[5, 10, 15, 20, 30].map(n => `<option value="${n}"${SC.sec === n ? ' selected' : ''}>${n} s</option>`).join('')}</select></span>`;
    if (at) at.insertAdjacentHTML('beforebegin', h); else bar.insertAdjacentHTML('beforeend', h);
    $('hxScan').onclick = () => scT ? scStop() : scStart();
    $('hxScS').onchange = () => { SC.sec = +$('hxScS').value; SV('kpcHuntScan', SC); if (scT) { clearInterval(scT); scT = setInterval(scStep, SC.sec * 1000); } };
  }
  const scList = () => (G.KPCHuntShown || []).filter(s => s && !/^FT[48]$/i.test(s.mode || '') && +s.khz > 0);
  function scStart() {
    if (!scList().length) { note('Nothing to scan: no voice or CW spots shown.', true); return; }
    scI = -1; scK = ''; scStep(); scT = setInterval(scStep, SC.sec * 1000);
    $('hxScan').textContent = '⏹ STOP SCAN'; $('hxScan').classList.add('on');
    note(conn() ? '▶ Scanning: the radio goes to each spot. Tap ⏹ to stop.' : '▶ Scanning the list (no radio connected: highlighting only).');
  }
  function scStop(why) {
    clearInterval(scT); scT = 0; document.querySelectorAll('.hx-scanon').forEach(e => e.classList.remove('hx-scanon'));
    const b = $('hxScan'); if (b) { b.textContent = '▶ SCAN'; b.classList.remove('on'); } if (why) note(why);
  }
  function scStep() {
    const L = scList(); if (!L.length) { scStop('Scan stopped: no voice or CW spots shown.'); return; }
    let i = scK ? L.findIndex(s => KPCHunt.keyOf(s) === scK) : -1; i = (i + 1) % L.length; const s = L[i]; scK = KPCHunt.keyOf(s);
    document.querySelectorAll('.hx-scanon').forEach(e => e.classList.remove('hx-scanon'));
    const el = document.querySelector(`#hlSpots [data-k="${CSS.escape(scK)}"], #hlFavs [data-k="${CSS.escape(scK)}"]`);
    if (el) { el.classList.add('hx-scanon'); try { el.scrollIntoView({ block: 'nearest', behavior: 'smooth' }); } catch (e) {} }
    if (conn() && K().get().on) { try { KPCHunt.fill(s); } catch (e) {} }
  }
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && scT) scStop('Scan stopped.'); });
  if ($('dCall')) $('dCall').addEventListener('input', () => { if (scT && $('dCall').value.trim()) scStop('Scan stopped: you are logging.'); });

  /* ================================================================ ⚙ THE RADIO WINDOW */
  const PS = Object.assign({ tab: 'radio', x: null, y: null }, LS('kpcHuntPop', {}));
  const TABS = [['radio', '📻 Radio'], ['meters', '📊 Meters'], ['band', '📍 Bands · Tune · SWR'], ['audio', '🎧 Audio · Mic'], ['more', '🎛 More'], ['cw', '📟 CW']];
  const SHOWS = { band: ['lrBand'], audio: ['lrHear'], more: ['lrMore', 'lrScope', 'lrGuide'] };
  function gearMount() {
    const top = document.querySelector('#dkForm .dk-top'); if (!top || $('hxGear')) return;
    const at = $('dkRad') || top.lastChild;
    at.insertAdjacentHTML('beforebegin', '<button type="button" class="dk-rad" id="hxGear" title="Radio controls: connect, meters, bands, tune, audio, more, CW">⚙</button><button type="button" class="dk-rad" id="hxCwB" title="CW memory keyer" hidden>📟</button>');
    $('hxGear').onclick = () => (POP && !POP.hidden ? close() : open());
    $('hxCwB').onclick = () => open('cw');
  }
  let POP = null;
  function build() {
    if (POP) return POP;
    document.body.insertAdjacentHTML('beforeend', `<div class="hx-pop" id="hxPop" role="dialog" aria-label="Radio controls" hidden>
      <div class="hx-bar" id="hxBar"><b>⚙ RADIO</b><span id="hxSt"></span><button type="button" class="hx-x" id="hxX" aria-label="Close">✕</button></div>
      <div class="hx-tabs" id="hxTabs">${TABS.map(([k, l]) => `<button type="button" data-hxt="${k}">${l}</button>`).join('')}</div>
      <div class="hx-body" id="hxBody"><div id="hxPane"></div><div id="hxHost"></div><div id="hxTx"></div></div></div>`);
    POP = $('hxPop');
    $('hxX').onclick = () => close();
    $('hxTabs').onclick = e => { const b = e.target.closest('[data-hxt]'); if (b) show(b.dataset.hxt); };
    drag();
    return POP;
  }
  function open(tab) {
    build(); POP.hidden = false; place(); show(tab || PS.tab || 'radio');
  }
  function close() {
    if (!POP) return; POP.hidden = true; talkUp();
    const box = LR() && LR().box, home = LR() && LR().home && LR().home();
    if (box && home && box.parentNode !== home) { home.appendChild(box); box.removeAttribute('data-hxtab'); try { LR().draw(); } catch (e) {} }
    else if (box && box.parentNode === $('hxHost')) box.remove();
  }
  function show(tab) {
    PS.tab = tab; SV('kpcHuntPop', PS);
    POP.dataset.tab = tab; POP.querySelectorAll('[data-hxt]').forEach(b => b.classList.toggle('on', b.dataset.hxt === tab));
    const box = LR() && LR().box, host = $('hxHost'), pane = $('hxPane'), tx = $('hxTx');
    pane.innerHTML = ''; tx.innerHTML = '';
    if (SHOWS[tab] && box) {
      if (box.parentNode !== host) host.appendChild(box);
      box.dataset.hxtab = tab; try { LR().draw(); } catch (e) {}
      SHOWS[tab].forEach(id => { const d = $(id); if (d) d.open = true; });
      if (!conn()) pane.innerHTML = '<p class="hx-n">Connect the radio first (📻 Radio tab). These go to the radio over CAT.</p>';
    } else if (box && box.parentNode === host) {
      const home = LR().home && LR().home(); if (home) { home.appendChild(box); box.removeAttribute('data-hxtab'); try { LR().draw(); } catch (e) {} } else box.remove();
    }
    if (SHOWS[tab] && !box) pane.innerHTML = '<p class="hx-n">The radio extras did not load on this page.</p>';
    if (tab === 'radio') radioPane(pane);
    if (tab === 'meters') metersPane(pane);
    if (tab === 'audio') txPane(tx);
    if (tab === 'cw') cwPane(pane);
    stat();
  }
  function place() {
    const W = Math.min(440, innerWidth - 16);
    POP.style.width = W + 'px';
    let x = PS.x, y = PS.y;
    if (x == null || y == null) { x = innerWidth - W - 12; y = 70; }
    x = Math.max(4, Math.min(innerWidth - W - 4, x)); y = Math.max(4, Math.min(innerHeight - 120, y));
    POP.style.left = x + 'px'; POP.style.top = y + 'px';
  }
  function drag() {
    const bar = $('hxBar'); let sx = 0, sy = 0, ox = 0, oy = 0, on = false;
    bar.addEventListener('pointerdown', e => { if (e.target.closest('button')) return; on = true; sx = e.clientX; sy = e.clientY; ox = POP.offsetLeft; oy = POP.offsetTop; try { bar.setPointerCapture(e.pointerId); } catch (x) {} });
    bar.addEventListener('pointermove', e => { if (!on) return; PS.x = ox + e.clientX - sx; PS.y = oy + e.clientY - sy; place(); });
    const up = () => { if (on) { on = false; SV('kpcHuntPop', PS); } };
    bar.addEventListener('pointerup', up); bar.addEventListener('pointercancel', up);
    addEventListener('resize', () => { if (POP && !POP.hidden) place(); });
  }
  function stat() { const s = $('hxSt'); if (!s) return; const k = K(); s.textContent = !k ? 'radio control not on this page' : conn() ? '● ' + ((k.RADIO || {})[k.get().radio] || {}).label || '● connected' : '○ not connected'; s.className = conn() ? 'on' : ''; }

  /* ---- 📻 Radio: pick, connect, frequency, mode ---- */
  function radioPane(p) {
    const k = K();
    if (!k) { p.innerHTML = '<p class="hx-n">Radio control is not on this page.</p>'; return; }
    if (!k.supported()) { p.innerHTML = '<p class="hx-n">This browser cannot talk to a radio. Use <b>Chrome</b> or <b>Edge</b> on a computer (or Chrome on Android), radio on its USB cable.</p>'; return; }
    const on = conn(), S = k.get();
    p.innerHTML = `<div class="hx-row"><label class="hx-l">MY RADIO<select id="hxRig"></select></label><button type="button" class="hx-b gold" id="hxConn">${on ? '✕ DISCONNECT' : '🔌 CONNECT'}</button></div>
      <div class="hx-row"><label class="hx-l">FREQUENCY (MHz)<input id="hxF" inputmode="decimal" placeholder="14.285"></label><label class="hx-l">MODE<select id="hxM">${['USB', 'LSB', 'CW', 'FM', 'AM', 'DATA'].map(m => `<option>${m}</option>`).join('')}</select></label><button type="button" class="hx-b" id="hxGo"${on ? '' : ' disabled'}>GO</button><button type="button" class="hx-b" id="hxRd"${on ? '' : ' disabled'}>READ</button></div>
      <label class="hx-t"><input type="checkbox" id="hxOn"${S.on ? ' checked' : ''}> Tune my radio when I click a spot</label>
      <p class="hx-n" id="hxRs">${on ? 'Connected.' : 'Pick your radio, plug in its USB cable, then 🔌 CONNECT (Chrome / Edge asks which port).'} Full setup and port help: ${$('ctCat') ? 'the 📻 RADIO CONTROL card on this page' : '<a href="kpc-hunt-cat.html">📻 CAT &amp; QRZ</a>'}.</p>`;
    k.fillSelect($('hxRig'));
    $('hxRig').onchange = () => { k.pickRadio($('hxRig').value); try { LR() && LR().draw(); } catch (e) {} };
    $('hxConn').onclick = async () => { if (conn()) { await k.disconnect(); } else { k.set({ on: true }); $('hxRs').textContent = 'Connecting…'; const ok = await k.connect(true); if (!ok) $('hxRs').textContent = 'The radio did not answer. Check MY RADIO and the cable, close other radio programs, and try again.'; } show('radio'); };
    $('hxOn').onchange = () => k.set({ on: $('hxOn').checked });
    $('hxGo').onclick = async () => { const f = parseFloat($('hxF').value); if (!(f > 0)) { note('Type a frequency in MHz, like 14.285', true); return; } const ok = await k.tune(f * 1000, $('hxM').value); note(ok ? '📻 ' + f + ' MHz ' + $('hxM').value : 'The radio did not take it.', !ok); };
    $('hxRd').onclick = rd;
    if (on) rd();
    async function rd() { const r = await k.read(); if (!$('hxF')) return; if (r && r.khz) { $('hxF').value = (r.khz / 1000).toFixed(4).replace(/0+$/, '').replace(/\.$/, ''); if (r.mode && [...$('hxM').options].some(o => o.value === r.mode)) $('hxM').value = r.mode; } }
  }
  /* ---- 📊 Meters ---- */
  function metersPane(p) {
    const has = !!G.KPCMeters;
    p.innerHTML = `<p class="hx-n">S-meter, power out, ALC and SWR from the radio, in their own window you can move and size.</p><div class="hx-row"><button type="button" class="hx-b gold" id="hxMet"${has ? '' : ' disabled'}>📊 OPEN THE METERS</button></div>${conn() ? '' : '<p class="hx-n">Connect the radio first (📻 Radio tab): the meters show — until then.</p>'}`;
    if (has) $('hxMet').onclick = () => KPCMeters.open();
  }

  /* ---- 🎧 Audio / Mic: talk from this computer ---- */
  const TX = Object.assign({ mic: '', out: '', voice: 'natural', db: 0, mg: 50, pw: 100, lim: 120 }, LS('kpcHuntTalk', {}));
  const txSave = () => SV('kpcHuntTalk', TX);
  const VP = { natural: { hp: 80, pkHz: 2500, pkDb: 0, lp: 6000, th: -6, ratio: 1.2, mk: 1 }, punch: { hp: 250, pkHz: 2500, pkDb: 4, lp: 3400, th: -20, ratio: 4, mk: 1.3 }, contest: { hp: 350, pkHz: 2900, pkDb: 8, lp: 3000, th: -28, ratio: 10, mk: 1.8 } };
  function txPane(p) {
    const k = K(), lr = LR(), cmds = n => !!(lr && lr.cmds && conn() && lr.cmds(n, 50));
    const sink = 'setSinkId' in HTMLMediaElement.prototype;
    p.innerHTML = `<div class="hx-h">🎙 TALK FROM THIS COMPUTER</div>
      <div class="hx-row"><label class="hx-l">MIC<select id="hxMic"><option value="">this computer's microphone</option></select></label><label class="hx-l">TO THE RADIO<select id="hxOut"${sink ? '' : ' disabled'}><option value="">pick the radio's USB sound…</option></select></label></div>
      <div class="hx-row"><span class="hx-k">VOICE</span>${Object.keys(VP).map(v => `<button type="button" class="hx-c${TX.voice === v ? ' on' : ''}" data-hxv="${v}">${v.toUpperCase()}</button>`).join('')}</div>
      <div class="hx-row"><span class="hx-k">MIC LEVEL</span><input type="range" id="hxDb" min="-10" max="20" step="1" value="${TX.db}"><span class="hx-v" id="hxDbT">${TX.db > 0 ? '+' : ''}${TX.db} dB</span></div>
      <div class="hx-row"${cmds('mic') ? '' : ' hidden'}><span class="hx-k">RADIO MIC GAIN</span><input type="range" id="hxMg" min="0" max="100" step="5" value="${TX.mg}"><span class="hx-v" id="hxMgT">${TX.mg}</span></div>
      <div class="hx-row"${cmds('power') ? '' : ' hidden'}><span class="hx-k">RF POWER</span><input type="range" id="hxPw" min="5" max="100" step="5" value="${TX.pw}"><span class="hx-v" id="hxPwT">${TX.pw} %</span></div>
      <button type="button" class="hx-talk" id="hxTalk"${conn() ? '' : ' disabled'}>🎙 HOLD TO TALK <small>(this computer's microphone)</small></button>
      <p class="hx-n">${conn() ? '' : 'Connect the radio first (📻 Radio tab). '}The radio keys over CAT while you hold the button. Its SSB MOD SOURCE menu must be REAR / USB so it takes this sound.${sink ? '' : ' Picking TO THE RADIO works in Chrome and Edge; here the sound goes to the default speaker.'} Let go = back to receive (limit ${TX.lim} s).</p>`;
    fillDev();
    p.querySelectorAll('[data-hxv]').forEach(b => { b.onclick = () => { TX.voice = b.dataset.hxv; txSave(); p.querySelectorAll('[data-hxv]').forEach(x => x.classList.toggle('on', x === b)); if (TK && TK.shape) TK.shape(TX.voice); }; });
    $('hxDb').oninput = () => { TX.db = +$('hxDb').value; $('hxDbT').textContent = (TX.db > 0 ? '+' : '') + TX.db + ' dB'; txSave(); if (TK && TK.vg) TK.vg.gain.value = Math.pow(10, TX.db / 20); };
    $('hxMg').oninput = () => { $('hxMgT').textContent = $('hxMg').value; }; $('hxMg').onchange = () => { TX.mg = +$('hxMg').value; txSave(); lr.send('mic', TX.mg); };
    $('hxPw').oninput = () => { $('hxPwT').textContent = $('hxPw').value + ' %'; }; $('hxPw').onchange = () => { TX.pw = +$('hxPw').value; txSave(); lr.send('power', TX.pw); };
    $('hxMic').onchange = () => { TX.mic = $('hxMic').value; txSave(); cool(true); };
    $('hxOut').onchange = () => { TX.out = $('hxOut').value; txSave(); };
    const t = $('hxTalk');
    t.addEventListener('pointerdown', e => { e.preventDefault(); try { t.setPointerCapture(e.pointerId); } catch (x) {} talkDown(); });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(n => t.addEventListener(n, () => talkUp()));
    t.addEventListener('contextmenu', e => e.preventDefault());
  }
  async function fillDev() {
    const i = $('hxMic'), o = $('hxOut'); if (!i || !navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    try { const ds = await navigator.mediaDevices.enumerateDevices();
      const opt = (d, cur) => `<option value="${esc(d.deviceId)}"${d.deviceId === cur ? ' selected' : ''}>${esc(d.label || d.kind + ' ' + d.deviceId.slice(0, 4))}</option>`;
      i.innerHTML = '<option value="">this computer\'s microphone</option>' + ds.filter(d => d.kind === 'audioinput').map(d => opt(d, TX.mic)).join('');
      if (!o.disabled) o.innerHTML = '<option value="">pick the radio\'s USB sound…</option>' + ds.filter(d => d.kind === 'audiooutput').map(d => opt(d, TX.out)).join('');
    } catch (e) {}
  }
  let TK = null; const WARM = { st: null, dev: '', t: 0 };
  function cool(now) { clearTimeout(WARM.t); WARM.t = setTimeout(() => { if (WARM.st && !TK) { WARM.st.getTracks().forEach(x => x.stop()); WARM.st = null; } }, now ? 0 : 60000); }
  async function talkDown() {
    if (TK) return; const k = K();
    if (!conn()) { note('Connect the radio first (📻 Radio tab).', true); return; }
    const me = TK = { key: k.ptt(true, 'cat') };   /* key at once, while the mic opens (the KPC app's Nov 8 fix) */
    $('hxTalk').classList.add('on');
    try {
      clearTimeout(WARM.t);
      let st = WARM.st && WARM.dev === TX.mic && WARM.st.getAudioTracks().some(t => t.readyState === 'live') ? WARM.st : null;
      if (!st) { if (WARM.st) WARM.st.getTracks().forEach(t => t.stop()); st = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: TX.mic ? { exact: TX.mic } : undefined, echoCancellation: false, noiseSuppression: true, autoGainControl: true } }); WARM.st = st; WARM.dev = TX.mic; }
      if (TK !== me) { cool(); return; }
      const c = me.ctx = new AudioContext(), src = c.createMediaStreamSource(st);
      const hp = c.createBiquadFilter(), pk = c.createBiquadFilter(), lp = c.createBiquadFilter(), comp = c.createDynamicsCompressor(), mk = c.createGain(), vg = c.createGain(), gate = c.createGain();
      hp.type = 'highpass'; pk.type = 'peaking'; lp.type = 'lowpass'; gate.gain.value = 0; vg.gain.value = Math.pow(10, TX.db / 20);
      me.shape = n => { const q = VP[n] || VP.natural; hp.frequency.value = q.hp; pk.frequency.value = q.pkHz; pk.Q.value = 1.1; pk.gain.value = q.pkDb; lp.frequency.value = q.lp; comp.threshold.value = q.th; comp.ratio.value = q.ratio; comp.attack.value = 0.003; comp.release.value = 0.12; comp.knee.value = 6; mk.gain.value = q.mk; };
      me.shape(TX.voice); me.vg = vg; me.gate = gate;
      src.connect(hp); hp.connect(pk); pk.connect(lp); lp.connect(comp); comp.connect(mk); mk.connect(vg); vg.connect(gate);
      if (TX.out && 'setSinkId' in HTMLMediaElement.prototype) { const d = c.createMediaStreamDestination(); gate.connect(d); me.el = new Audio(); me.el.srcObject = d.stream; await me.el.setSinkId(TX.out).catch(() => {}); await me.el.play().catch(() => {}); }
      else gate.connect(c.destination);
      const ok = await me.key; if (TK !== me) return; if (!ok) throw new Error('the radio did not key');
      gate.gain.value = 1;
      me.lim = setTimeout(() => { talkUp(); note('🎙 Talk limit: let go.'); }, TX.lim * 1000);
    } catch (e) { note('🎙 ' + (e.message || e), true); talkUp(); }
  }
  async function talkUp() {
    const t = TK; if (!t) return; TK = null; clearTimeout(t.lim); const b = $('hxTalk'); if (b) b.classList.remove('on');
    try { if (t.gate) t.gate.gain.value = 0; } catch (e) {} try { if (t.el) t.el.pause(); } catch (e) {} try { if (t.ctx) t.ctx.close(); } catch (e) {}
    cool(); if (t.key) { await t.key; await K().ptt(false, 'cat'); }
  }
  G.addEventListener('blur', () => talkUp());

  /* ---- 📟 CW memory keyer ---- */
  const CW = Object.assign({ m: ['CQ POTA DE {MY} {MY} K', '{CALL} TU 5NN KY', '{MY}', 'TU 73', 'AGN?', 'QRZ?'], wpm: 22 }, LS('kpcHuntCw', {}));
  const cwSave = () => SV('kpcHuntCw', CW);
  const myCall = () => { try { const v = localStorage.getItem('kpcMyCall'); return String(v ? (v[0] === '"' ? JSON.parse(v) : v) : '').toUpperCase(); } catch (e) { return ''; } };
  const fillTxt = t => String(t || '').replace(/\{CALL\}/g, (($('dCall') && $('dCall').value) || '').split(/[\s,;]+/)[0].toUpperCase()).replace(/\{MY\}/g, myCall()).replace(/\s+/g, ' ').trim();
  function cwPane(p) {
    const k = K(), on = conn(), can = on && k.cwCan && k.cwCan();
    if (!on) { p.innerHTML = '<p class="hx-n">Connect the radio first (📻 Radio tab). The CW keyer uses the radio\'s own keyer over CAT.</p>'; return; }
    p.innerHTML = `${can ? '' : '<p class="hx-n">This radio can\'t take typed CW over CAT (older Yaesu, Xiegu…). Use a CW key line or the radio\'s own keyer memories.</p>'}
      <div class="hx-mem${can ? '' : ' off'}">${CW.m.map((m, i) => `<button type="button" class="hx-c" data-cwm="${i}" title="${esc(m)}"${can ? '' : ' disabled'}>M${i + 1} <small>${esc(m.slice(0, 14))}</small></button>`).join('')}</div>
      <div class="hx-row"><input id="hxCwT" placeholder="type CW to send, Enter sends" maxlength="120"${can ? '' : ' disabled'}><button type="button" class="hx-b gold" id="hxCwGo"${can ? '' : ' disabled'}>SEND</button><button type="button" class="hx-b" id="hxCwStop"${can ? '' : ' disabled'}>⏹ STOP</button></div>
      <div class="hx-row"><span class="hx-k">WPM</span><input type="range" id="hxWpm" min="6" max="48" step="1" value="${CW.wpm}"${can ? '' : ' disabled'}><span class="hx-v" id="hxWpmT">${CW.wpm}</span></div>
      <details class="hx-ed"><summary>✏ EDIT THE MEMORIES</summary>${CW.m.map((m, i) => `<label class="hx-l">M${i + 1}<input data-cwe="${i}" value="${esc(m)}" maxlength="80"></label>`).join('')}<p class="hx-n">{CALL} = the (first) call in the log box · {MY} = your call.</p></details>`;
    p.querySelectorAll('[data-cwm]').forEach(b => { b.onclick = () => cwSend(fillTxt(CW.m[+b.dataset.cwm])); });
    $('hxCwGo').onclick = () => { const v = $('hxCwT').value; if (v.trim()) { cwSend(fillTxt(v)); $('hxCwT').value = ''; } };
    $('hxCwT').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('hxCwGo').click(); } };
    $('hxCwStop').onclick = () => { k.cwStop && k.cwStop(); note('⏹ CW stopped.'); };
    $('hxWpm').oninput = () => { $('hxWpmT').textContent = $('hxWpm').value; }; $('hxWpm').onchange = () => { CW.wpm = +$('hxWpm').value; cwSave(); };
    p.querySelectorAll('[data-cwe]').forEach(inp => { inp.onchange = () => { CW.m[+inp.dataset.cwe] = inp.value.toUpperCase(); cwSave(); }; });
  }
  async function cwSend(t) {
    if (!t) { note('Nothing to send (is the call box empty?).', true); return; }
    const k = K(); if (!conn() || !(k.cwCan && k.cwCan())) { note('Connect a radio that takes typed CW first.', true); return; }
    const ok = await k.cw(t, CW.wpm); note(ok ? '📟 ' + t : 'The radio did not take the CW.', !ok);
  }

  /* ================================================================ keep things in step with the radio */
  function radioState() {
    const on = conn(), k = K(), cwb = $('hxCwB');
    if (cwb) cwb.hidden = !(on && k.cwCan && k.cwCan());
    stat();
    /* redraw the open tab only when connected / not connected really changed, and never while talking or typing in it */
    if (on !== radioState.was) { radioState.was = on; const ae = document.activeElement;
      if (POP && !POP.hidden && !TK && !(ae && POP.contains(ae) && /^(INPUT|SELECT|TEXTAREA)$/.test(ae.tagName)) && ['radio', 'cw', 'audio', 'meters', 'band', 'more'].includes(PS.tab)) show(PS.tab); }
  }
  function hook() { const k = K(); if (k && k.onStatus && !hook.done) { hook.done = 1; k.onStatus(() => setTimeout(radioState, 350)); } }

  /* ================================================================ START */
  const css = document.createElement('style');
  css.textContent = `.hx-scan.on{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05}.hx-scg{display:inline-flex;align-items:stretch;white-space:nowrap}.hx-scg .hx-scs{font:800 13px Arial,sans-serif;padding:0 6px;min-height:0}.hx-scs{margin-left:4px;min-height:30px;background:#140d06;color:#f3e6c8;border:1px solid rgba(240,201,107,.5);border-radius:8px}
.hx-scanon{outline:3px solid #f6d58a!important;outline-offset:2px;box-shadow:0 0 18px rgba(246,213,138,.55)!important}
.hx-pop{position:fixed;z-index:9990;max-height:min(80vh,640px);display:flex;flex-direction:column;background:#140d06;border:1px solid #f0c96b;border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.6);color:#f3e6c8;font:14px Arial,sans-serif}
.hx-pop[hidden]{display:none}.hx-bar{display:flex;align-items:center;gap:8px;padding:8px 10px;cursor:move;border-bottom:1px solid rgba(240,201,107,.35);user-select:none;touch-action:none}
.hx-bar b{font:900 12.5px Arial;letter-spacing:1.3px;color:#ffcf7a}.hx-bar span{flex:1;font-size:12px;color:#cdbb98}.hx-bar span.on{color:#9be59b}.hx-x{min-width:34px;min-height:32px;border:1px solid rgba(240,201,107,.5);border-radius:8px;background:#0d0904;color:#f3e6c8;cursor:pointer}
.hx-tabs{display:flex;flex-wrap:wrap;gap:4px;padding:6px 8px;border-bottom:1px solid rgba(240,201,107,.2)}.hx-tabs button{min-height:32px;padding:4px 9px;border:1px solid rgba(240,201,107,.4);border-radius:999px;background:#0d0904;color:#f3e6c8;font:800 11.5px Arial;cursor:pointer}
.hx-tabs button.on{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05}.hx-body{overflow:auto;padding:8px 12px 12px}
.hx-row{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:7px 0}.hx-row[hidden]{display:none}.hx-l{display:flex;flex-direction:column;gap:3px;font:900 10.5px Arial;letter-spacing:1px;color:#e9c77d;flex:1 1 150px}
.hx-l input,.hx-l select,#hxCwT{min-height:36px;background:#0d0904;color:#f3e6c8;border:1px solid rgba(240,201,107,.5);border-radius:8px;padding:4px 8px;font:14px Arial}#hxCwT{flex:1 1 180px;text-transform:uppercase}
.hx-b,.hx-c{min-height:36px;padding:6px 12px;border:1px solid rgba(240,201,107,.5);border-radius:999px;background:#140d06;color:#f3e6c8;font:800 12.5px Arial;cursor:pointer}.hx-b.gold,.hx-c.on{background:linear-gradient(90deg,#f6d58a,#d5a63a);color:#2a1a05;border-color:#f6d58a}.hx-b:disabled,.hx-c:disabled{opacity:.45;cursor:default}
.hx-k{min-width:96px;font:900 11px Arial;letter-spacing:1px;color:#e9c77d}.hx-v{min-width:56px;font:700 12.5px monospace;color:#ffe2a8}.hx-row input[type=range]{flex:1 1 150px;accent-color:#d5a63a}
.hx-n{margin:6px 0;color:#cdbb98;font-size:13px;line-height:1.4}.hx-n a{color:#ffcf7a}.hx-t{display:flex;gap:8px;align-items:center;margin:6px 0;font-size:13.5px}.hx-h{font:900 11px Arial;letter-spacing:1.2px;color:#e9c77d;margin:10px 0 2px}
.hx-talk{display:block;width:100%;min-height:54px;margin:8px 0;border:2px solid #f0c96b;border-radius:14px;background:#2a1708;color:#fff;font:900 16px Arial;cursor:pointer;touch-action:none;user-select:none}.hx-talk.on{background:#8a1d12;border-color:#ff8a7a}.hx-talk:disabled{opacity:.45}.hx-talk small{font-weight:400;font-size:12px}
.hx-mem{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:6px 0}.hx-mem .hx-c{border-radius:10px;text-align:left}.hx-mem small{display:block;font-weight:400;font-size:11px;opacity:.8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hx-ed summary{cursor:pointer;font:900 11px Arial;letter-spacing:1px;color:#e9c77d;margin:8px 0}
#hxHost #lrBox{margin:0}#hxHost #lrBox>details{display:none}#hxHost #lrBox[data-hxtab="band"]>#lrBand,#hxHost #lrBox[data-hxtab="audio"]>#lrHear,#hxHost #lrBox[data-hxtab="more"]>#lrMore,#hxHost #lrBox[data-hxtab="more"]>#lrScope,#hxHost #lrBox[data-hxtab="more"]>#lrGuide{display:block}
#hxMsg{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);z-index:99999;max-width:min(560px,92vw);padding:12px 16px;border-radius:12px;background:#1d1208;border:1px solid #f0c96b;color:#fff;font:700 14px Arial;box-shadow:0 6px 24px rgba(0,0,0,.5)}#hxMsg.bad{border-color:#ff8a7a;background:#2a0e0a}
@media (max-width:520px){.hx-pop{left:4px!important;right:4px;width:auto!important;top:auto!important;bottom:4px;max-height:78vh}.hx-mem{grid-template-columns:repeat(2,1fr)}}`;
  document.head.appendChild(css);
  clsMount(); scMount(); gearMount(); hook();
  /* kpc-cat.js may arrive after this file on some pages */
  let tries = 0; const t0 = setInterval(() => { hook(); radioState(); if (++tries > 20 || hook.done) clearInterval(t0); }, 500);
  redraw();
  G.KPCHuntX = { pass, allowed, CL, open, close, show, scStart, scStop, scanning: () => !!scT, cwSend, talkDown, talkUp };
})(window);
