/* KPC Logger: FT8 / FT4 tab (Brandon Oct 17 2026: 'add the wsjtx version into it… a tab so if click on ft8 station it tabs over
   to it and once contact is made it auto logs… in that screen it be completely normal ft8… a pop up showing it logged… short message
   that goes away').
   Works like WSJT-X: radio audio in (sound card / USB interface) → decode every 15 s (FT4 7.5 s) → Band Activity + Rx Frequency lists,
   tap a station to call it, auto sequence (grid → report → R+report → RR73 → 73), TX audio out + PTT (VOX, CAT, RTS or DTR via kpc-cat.js),
   the finished contact goes straight into the KPC Logger (window.KPCLog.add) with a small 'logged' note.
   Decoder/encoder = kpc-ft8.js + kpc-ft8.wasm (ft8_lib by Karlis Goba, MIT license).
   Settings: localStorage kpcFt8. Nothing is sent anywhere except the audio to your radio. */
(function () {
  const $ = id => document.getElementById(id);
  const get = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const put = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const root = $('cFt8'); if (!root) return;
  const LG = () => window.KPCLog || null;

  const DIAL = {
    FT8: { '160m': 1840, '80m': 3573, '60m': 5357, '40m': 7074, '30m': 10136, '20m': 14074, '17m': 18100, '15m': 21074, '12m': 24915, '10m': 28074, '6m': 50313, '2m': 144174 },
    CW: { '160m': 1810, '80m': 3530, '60m': 5332, '40m': 7030, '30m': 10110, '20m': 14060, '17m': 18080, '15m': 21060, '12m': 24910, '10m': 28060, '6m': 50090 },
    FT4: { '80m': 3575, '40m': 7047.5, '30m': 10140, '20m': 14080, '17m': 18104, '15m': 21140, '12m': 24919, '10m': 28180, '6m': 50318 },
    /* Oct 17 (Brandon: RTTY, PSK31, SSTV, WSPR; 'SSTV can have pre-programmed frequencies'). Dial = the radio's USB (LSB for SSTV on 80/40) */
    RTTY: { '80m': 3580, '40m': 7080, '30m': 10140, '20m': 14085, '17m': 18100, '15m': 21080, '12m': 24920, '10m': 28080 },
    PSK31: { '160m': 1838, '80m': 3580, '40m': 7070, '30m': 10142, '20m': 14070, '17m': 18100, '15m': 21070, '12m': 24920, '10m': 28120, '6m': 50290 },
    SSTV: { '80m': 3845, '40m': 7171, '20m': 14230, '17m': 18160, '15m': 21340, '12m': 24975, '10m': 28680, '6m': 50680, '2m (ISS)': 145800 },
    /* Feld Hell nets (hellschreiber.com, Oct 17): FHC 80 m Fridays 3585, 40 m Thursdays 7069.5, 30 m Wednesdays 10142.5, 17 m Saturday transatlantic 18098 */
    HELL: { '80m': 3585, '40m': 7069.5, '30m': 10142.5, '17m': 18098 },
    WSPR: { '160m': 1836.6, '80m': 3568.6, '60m': 5287.2, '40m': 7038.6, '30m': 10138.7, '20m': 14095.6, '17m': 18104.6, '15m': 21094.6, '12m': 24924.6, '10m': 28124.6, '6m': 50293, '2m': 144489 }
  };
  const isFT = () => S.mode === 'FT8' || S.mode === 'FT4';
  const isDG = () => /^(RTTY|PSK31|HELL|SSTV|WSPR)$/.test(S.mode);
  const DG = () => window.KPCDigiUI || null;
  const S = Object.assign({ mode: 'FT8', band: '20m', inDev: '', outDev: '', ptt: 'vox', txHz: 1500, rxHz: 1500, hold: true, auto: true, first: true, even: true, keepCq: false, cqw: 'POTA', lvl: 0.3, deep: false, wd: 2, cwHz: 600, cwWpm: 20, cwVia: 'cat', cwBw: 'auto', cwMac: null, aPark: true, aState: false, aGrid: false, watch: '', mm: 'hear' }, get('kpcFt8', {}));
  const saveS = () => put('kpcFt8', S);
  const slotLen = () => S.mode === 'FT4' ? 7.5 : 15;
  const stdK = () => (DIAL[S.mode] || DIAL.FT8)[S.band] || DIAL.FT8['20m'];
  /* Oct 18 (Brandon: 'cw decoder no way to change frequency'): your own dial per mode + band (S.ov), set by the tune row or read from the radio's knob */
  const ovKey = () => S.mode + '|' + S.band;
  const dialK = () => (S.ov && S.ov[ovKey()]) || stdK();
  const BANDR = [['160m', 1800, 2000], ['80m', 3500, 4000], ['60m', 5330, 5410], ['40m', 7000, 7300], ['30m', 10100, 10150], ['20m', 14000, 14350], ['17m', 18068, 18168], ['15m', 21000, 21450], ['12m', 24890, 24990], ['10m', 28000, 29700], ['6m', 50000, 54000], ['2m', 144000, 148000]];
  const bandOfK = k => { const b = BANDR.find(r => k >= r[1] && k <= r[2]); return b ? b[0] : null; };
  const nowS = () => Date.now() / 1000;
  const utc = (t, sec) => { const d = new Date(t * 1000); const p = n => String(n).padStart(2, '0'); return p(d.getUTCHours()) + p(d.getUTCMinutes()) + (sec ? p(d.getUTCSeconds()) : ''); };
  const clean = c => String(c || '').replace(/[<>]/g, '').toUpperCase();
  const isGrid = t => /^[A-R]{2}\d{2}$/i.test(t) && t.toUpperCase() !== 'RR73';
  const isRpt = t => /^[+-]\d{2}$/.test(t);
  const isRRpt = t => /^R[+-]\d{2}$/.test(t);
  const fmtDb = n => (n >= 0 ? '+' : '-') + String(Math.min(49, Math.abs(Math.round(n)))).padStart(2, '0');

  /* ---------------- screen ---------------- */
  root.innerHTML = `
  <div class="f8-top">
    <button type="button" class="f8-back" id="f8Back">← LOGGER</button>
    <div class="f8-modes" role="group" aria-label="Mode"><button type="button" data-f8m="FT8">FT8</button><button type="button" data-f8m="FT4">FT4</button><button type="button" data-f8m="CW">CW</button><button type="button" data-f8m="RTTY">RTTY</button><button type="button" data-f8m="PSK31">PSK31</button><button type="button" data-f8m="HELL" title="Feld Hellschreiber">HELL</button><button type="button" data-f8m="SSTV">SSTV</button><button type="button" data-f8m="WSPR">WSPR</button></div>
    <select id="f8Band" aria-label="Band"></select>
    <b class="f8-dial" id="f8Dial">14.074 000</b>
    <span class="f8-clk"><b id="f8Utc">--:--:--</b><i class="f8-slot"><i id="f8SlotBar"></i></i></span>
    <span class="f8-st" id="f8St">OFF</span>
  </div>
  <div class="f8-bandr" id="f8BandR" role="group" aria-label="Jump to a band"></div>
  <div class="f8-tunr" id="f8TuneR"><span>MY DIAL</span><button type="button" class="f8-b" data-f8st="-1">−1</button><button type="button" class="f8-b" data-f8st="-0.1">−.1</button><input id="f8Khz" inputmode="decimal" aria-label="Dial frequency in kHz" placeholder="kHz"><b>kHz</b><button type="button" class="f8-b" data-f8st="0.1">+.1</button><button type="button" class="f8-b" data-f8st="1">+1</button><button type="button" class="f8-b" id="f8Std" title="Back to the usual frequency for this mode and band">↺ USUAL</button><small id="f8TuneT">Type a frequency, or turn the radio's knob (CAT connected) and it follows.</small></div>
  <div class="f8-startbox" id="f8StartBox"><button type="button" class="f8-go" id="f8Start">🎧 START LISTENING</button><span>Plug your radio's audio into this phone or computer (USB sound card / Digirig / the radio's USB), then press START. The browser asks to use the "microphone": that is how the radio's audio comes in.<label class="f8-in0">RADIO AUDIO IN <select id="f8In0"><option value="">Default input</option></select></label></span></div>
  <div class="f8-wfw"><canvas id="f8Wf" height="150"></canvas><canvas id="f8Scale" height="18"></canvas></div>
  <section class="cw-pane" id="cwPane" aria-label="CW decoder and keyboard">
    <div class="cw-top"><b>CW</b> <span>PITCH <b id="cwHzT">600</b> Hz</span><span>SPEED <b id="cwWpmT">--</b> WPM</span><span>SIGNAL <b id="cwSnT">--</b></span>
      <label class="ck"><input type="checkbox" id="cwAfc"> Follow the strongest signal</label>
      <select id="cwBw" aria-label="Filter"><option value="auto">Filter: auto</option><option value="50">50 Hz</option><option value="100">100 Hz</option><option value="200">200 Hz</option></select>
      <button type="button" class="f8-b" id="cwClr">CLEAR</button></div>
    <div class="cw-rx" id="cwRx" aria-live="polite"></div>
    <div class="cw-calls" id="cwCalls"></div>
    <div class="cw-log"><label>THEIR CALL<input id="cwCall" autocapitalize="characters" spellcheck="false"></label><label>SENT<input id="cwRs" value="599" maxlength="3"></label><label>RCVD<input id="cwRr" value="599" maxlength="3"></label><label>THEIR PARK<input id="cwRef" autocapitalize="characters" spellcheck="false" placeholder="optional"></label><button type="button" class="f8-b tx" id="cwLog">⬆ LOG IT</button></div>
    <div class="cw-mac" id="cwMac"></div>
    <div class="cw-txl"><input id="cwTx" placeholder="Type here and press Enter to send it as CW" autocapitalize="characters" spellcheck="false" autocomplete="off"><button type="button" class="f8-b tx" id="cwSend">SEND</button><button type="button" class="f8-b halt" id="cwStop">STOP</button></div>
    <div class="cw-set"><label>SEND SPEED<input type="number" id="cwWpm" min="8" max="45" value="20"> WPM</label>
      <label>TONE<input type="number" id="cwTone" min="300" max="1200" step="10" placeholder="same"> Hz <small>(audio-tone way; blank = the pitch you're listening to, so you land on their frequency)</small></label>
      <label class="ck"><input type="checkbox" id="cwAbbr"> ✂ Shorthand: turn words into CW short forms (THANK YOU → TU, YOUR → UR, PLEASE → PSE…)</label>
      <label>SEND WITH<select id="cwVia"><option value="cat">The radio's own keyer (CAT: Icom, Kenwood, Elecraft, QRP Labs)</option><option value="dtr">Key line DTR (Digirig and many cables)</option><option value="rts">Key line RTS</option><option value="audio">Audio tone (radio in USB/DATA, VOX or PTT)</option></select></label>
      <span class="cw-sending" id="cwSending"></span></div>
  </section>
  <div class="f8-lists">
    <section><h3>BAND ACTIVITY <small id="f8Cnt"></small><button type="button" class="f8-pf" id="f8PotaF" title="Show only park activators (POTA, WWFF, SOTA)">🌲 PARKS ONLY</button></h3><div class="f8-list" id="f8Band1"></div></section>
    <section><h3>RX FREQUENCY · MY QSO <small id="f8RxHz"></small></h3><div class="f8-list" id="f8Rx"></div></section>
  </div>
  <details class="f8-mapw" id="f8MapW"><summary>🗺 MAP <span class="f8-mm" role="group"><button type="button" data-mm="hear" class="on">📡 WHO I HEAR</button><button type="button" data-mm="me">📍 WHO HEARS ME</button><button type="button" data-mm="both">BOTH</button></span><small id="f8MapT"></small><small id="f8PskT"></small></summary><div id="f8Map" role="region" aria-label="Map of FT8 stations"></div><p class="f8-maph">Green = calling CQ · ring = park activator · red = calling you · blue = others · orange ▲ = stations that heard YOU (PSK Reporter, after you transmit) · gold ★ = you. Tap a dot to call them.</p></details>
  <div class="f8-ctl">
    <label>DX CALL<input id="f8Dx" autocomplete="off" autocapitalize="characters" spellcheck="false"></label>
    <label>DX GRID<input id="f8DxG" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="6"></label>
    <label>REPORT<input id="f8Rpt" inputmode="numeric" maxlength="3"></label>
    <button type="button" class="f8-b gen" id="f8Gen" title="Make the six messages again">GENERATE</button>
    <button type="button" class="f8-b tx" id="f8En">ENABLE TX</button>
    <button type="button" class="f8-b halt" id="f8Halt">HALT TX</button>
    <button type="button" class="f8-b" id="f8Tune">TUNE</button>
    <button type="button" class="f8-b cq" id="f8Cq">📣 CQ</button>
  </div>
  <div class="f8-chks">
    <label><input type="checkbox" id="f8Auto"> Auto seq</label>
    <label><input type="checkbox" id="f8First"> Call 1st</label>
    <label><input type="checkbox" id="f8Even"> Tx even/1st</label>
    <label><input type="checkbox" id="f8Hold"> Hold Tx freq</label>
    <label><input type="checkbox" id="f8Keep"> Keep calling CQ after each contact</label>
    <label class="hz">TX <input id="f8TxHz" inputmode="numeric" maxlength="4"> Hz</label>
    <label class="hz">RX <input id="f8RxHzIn" inputmode="numeric" maxlength="4"> Hz</label>
  </div>
  <div class="f8-txm" id="f8Txm"></div>
  <details class="f8-set" id="f8Set"><summary>⚙ AUDIO, PTT &amp; SETTINGS</summary>
    <div class="f8-sg">
      <label>RADIO AUDIO IN<select id="f8In"><option value="">Default input</option></select></label>
      <label>RX LEVEL<span class="f8-meter"><i id="f8Lvl"></i></span><small id="f8LvlT">aim for 30-60 dB</small></label>
      <label>RX GAIN <b id="f8RxgT"></b><span class="f8-pwr"><button type="button" class="f8-b" id="f8RxgD" title="2 dB down">−</button><input type="range" id="f8Rxg" min="-30" max="20" step="1" aria-label="RX gain in dB"><button type="button" class="f8-b" id="f8RxgU" title="2 dB up">+</button></span><small>Turns the radio's sound up or down in here. Best: set the radio's USB audio out level so RX LEVEL reads good at 0 dB.</small></label>
      <label>RADIO AUDIO OUT<select id="f8Out"><option value="">Default output</option></select><small id="f8OutT"></small></label>
      <label>TX LEVEL <b id="f8PwrT"></b><span class="f8-pwr"><button type="button" class="f8-b" id="f8PwrD" title="0.5 dB down">−</button><input type="range" id="f8Pwr" min="-40" max="0" step="0.5" aria-label="TX level in dB"><button type="button" class="f8-b" id="f8PwrU" title="0.5 dB up">+</button></span><small>Press TUNE, then − / + (0.5 dB steps; changes right away) until the radio's ALC barely moves. Not enough at 0 dB? Turn this tablet / phone's media volume all the way up, then the radio's USB MOD GAIN. ALC high but low power = too much audio: come down here first.</small></label>
      <label>PTT (KEYING THE RADIO)<select id="f8Ptt"><option value="vox">VOX (radio or interface keys on the audio)</option><option value="cat">CAT command (radio connected by USB)</option><option value="rts">RTS line (Digirig and many cables)</option><option value="dtr">DTR line</option></select></label>
      <label>CQ<select id="f8Cqw"><option value="">CQ</option><option value="POTA">CQ POTA</option><option value="SOTA">CQ SOTA</option><option value="WWFF">CQ WWFF</option></select></label>
      <label>STOP CALLING AFTER (NO ANSWER)<select id="f8Wd"><option value="1">1 minute</option><option value="2">2 minutes</option><option value="3">3 minutes</option><option value="5">5 minutes</option><option value="10">10 minutes</option></select></label>
      <label>🔔 ALERT ME FOR<span class="f8-al"><label class="ck"><input type="checkbox" id="f8aPark"> Park activators calling CQ</label><label class="ck"><input type="checkbox" id="f8aState"> A state I haven't worked</label><label class="ck"><input type="checkbox" id="f8aGrid"> A grid I haven't worked</label></span></label>
      <label>🔔 WATCH FOR THESE CALLS<input id="f8Watch" placeholder="K4ABC, W9XYZ" autocapitalize="characters" spellcheck="false"></label>
      <label class="ck"><input type="checkbox" id="f8Deep"> Deeper decoding (finds weaker stations, uses more battery)</label>
      <div class="f8-catrow"><button type="button" class="f8-b" id="f8Mic">🎤 NO CABLE? USE THIS PHONE'S MIC + SPEAKER</button></div>
      <p class="f8-mic" id="f8MicT" hidden>Using the built-in mic and speaker: put the phone right next to the radio's speaker (radio volume about half), and the radio's mic close to the phone's speaker. Turn the radio's <b>VOX</b> on so it keys when the phone plays, and keep the room quiet. It works, but a cable (Digirig, the radio's USB) decodes far more stations.</p>
      <div class="f8-catrow"><button type="button" class="f8-b" id="f8Cat">📻 CONNECT MY RADIO (CAT)</button><span id="f8CatT"></span></div>
    </div>
    <p class="f8-help">How it works: it listens to the radio's audio and shows everyone it decodes each 15 seconds (FT4: 7.5 s). Tap a station to call them: the six messages fill in and TX turns on. With <b>Auto seq</b> on it answers by itself (grid → report → R-report → RR73 → 73) and the contact goes into your log as soon as it's complete. <b>📣 CQ</b> calls CQ (CQ POTA when you have a park number). Set the radio to USB (or DATA/USB-D), the dial on the FT8 frequency, and keep the TX audio low. Your computer's or phone's clock must be right within about a second (turn on "set time automatically"). Engine: ft8_lib by Karlis Goba (MIT license). Practice calls on this page: K4TEST.</p>
  </details>
  <div class="f8-note" id="f8Note" hidden></div>`;

  /* band + mode controls */
  function bandOpts() { const B = Object.keys(DIAL[S.mode]); if (!DIAL[S.mode][S.band]) { S.band = B.includes('20m') ? '20m' : B.includes('40m') ? '40m' : B[0]; saveS(); } $('f8Band').innerHTML = B.map(b => `<option${b === S.band ? ' selected' : ''}>${b}</option>`).join(''); bandChips(); }
  function bandChips() { const B = Object.keys(DIAL[S.mode]); $('f8BandR').innerHTML = B.map(b => `<button type="button" data-f8b="${b}"${b === S.band ? ' class="on"' : ''}>${b.replace(' (ISS)', ' ISS')}</button>`).join(''); }
  function goBand(b) { if (!DIAL[S.mode][b]) return; S.band = b; /* Oct 18 (Brandon: '40m goes to 7019.6'): a band button always means the usual dial; a frequency picked up from the radio's knob earlier is forgotten */ if (S.ov) delete S.ov[ovKey()]; saveS(); $('f8Band').value = b; bandChips(); showDial(); radioTune(); slotSep(true); }
  function showDial() { const k = dialK(); $('f8Dial').textContent = (k / 1000).toFixed(6).replace(/(\.\d{3})(\d{3})$/, '$1 $2'); $('f8Dial').classList.toggle('ov', !!(S.ov && S.ov[ovKey()])); if (document.activeElement !== $('f8Khz')) $('f8Khz').value = (+k.toFixed(3)).toString(); $('f8Std').hidden = !(S.ov && S.ov[ovKey()]); document.querySelectorAll('#f8BandR [data-f8b]').forEach(b => b.classList.toggle('on', b.dataset.f8b === S.band)); document.querySelectorAll('[data-f8m]').forEach(b => { b.classList.toggle('on', b.dataset.f8m === S.mode); if (b.dataset.f8m === S.mode && b.parentElement.scrollWidth > b.parentElement.clientWidth) b.parentElement.scrollLeft = b.offsetLeft - b.parentElement.clientWidth / 2 + b.offsetWidth / 2; }); }
  const radioMode = () => S.mode === 'CW' ? 'CW' : S.mode === 'SSTV' ? (S.band === '2m (ISS)' ? 'FM' : dialK() < 10000 ? 'LSB' : 'USB') : 'DATA';
  let tunedAt = 0;
  /* Oct 18 (Brandon: '40m preset does not put me on the right frequency'): after tuning, ask the radio where it is; try once more, then say what the radio shows */
  let tuneN = 0;
  function radioTune() { if (!(window.KPCCat && KPCCat.get().on)) return; tunedAt = Date.now(); const want = dialK(), md = radioMode(), my = ++tuneN;
    KPCCat.tune(want, md).then(async ok => { if (!ok || my !== tuneN) return;
      for (let i = 0; i < 2; i++) { await new Promise(r => setTimeout(r, 1300)); if (my !== tuneN) return; tunedAt = Date.now();
        const r = await KPCCat.read(); if (!r || !r.khz) return;
        if (Math.abs(r.khz - want) <= 0.05) { if (md === 'DATA' && /yaesu/.test(KPCCat.get().proto) && r.mode && r.mode !== 'DATA') note(`Radio is in ${r.mode}, not DATA mode: some radios then take the sound from the mic jack (low power). Set FT8 & digital modes to DATA mode under ⚙ Station → Radio control (or the CAT & QRZ tab).`); return; }
        if (i === 0) { tunedAt = Date.now(); await KPCCat.tune(want, md); } else note(`Radio shows ${(r.khz / 1000).toFixed(4)} MHz, not ${(want / 1000).toFixed(4)}. Check the radio's VFO A and that it is not locked or split.`); } }); }
  /* set my own dial (kHz); a frequency on another band switches the band when this mode has it */
  function setDial(k, fromRadio) {
    k = +k; if (!isFinite(k) || k <= 0) return; if (k < 1000) k *= 1000; k = Math.round(k * 1000) / 1000;
    const b = bandOfK(k); if (!b) { if (!fromRadio) note('That frequency is not on a ham band.'); showDial(); return; }
    if (b !== S.band) { if (!DIAL[S.mode][b]) { if (!fromRadio) note(`${S.mode} has no ${b} setting here.`); showDial(); return; } S.band = b; $('f8Band').value = b; slotSep(true); }
    S.ov = S.ov || {}; if (Math.abs(k - stdK()) < 0.0005) delete S.ov[ovKey()]; else S.ov[ovKey()] = k; saveS(); showDial(); if (!fromRadio) radioTune();
  }
  $('f8Dial').onclick = () => $('f8TuneR').classList.toggle('open'); $('f8Dial').title = 'Tap to change the frequency';
  $('f8TuneR').addEventListener('click', e => { const b = e.target.closest('[data-f8st]'); if (b) setDial(dialK() + +b.dataset.f8st); });
  $('f8Khz').onchange = () => setDial($('f8Khz').value.replace(',', '.'));
  $('f8Khz').onkeydown = e => { if (e.key === 'Enter') { e.preventDefault(); $('f8Khz').blur(); } };
  $('f8Std').onclick = () => { if (S.ov) delete S.ov[ovKey()]; saveS(); showDial(); radioTune(); };
  /* follow the radio's knob while CAT is connected (not right after we tuned it) */
  setInterval(async () => { if (root.hidden || document.hidden || !window.KPCCat || !KPCCat.get().on || !KPCCat.connected() || Date.now() - tunedAt < 4000 || document.activeElement === $('f8Khz') || TXING) return;
    try { const r = await KPCCat.read(); if (r && r.khz && Math.abs(r.khz - dialK()) > 0.02 && Date.now() - tunedAt >= 4000) setDial(r.khz, true); } catch (e) {} }, 2500);
  function setMode(m) { if (m === S.mode) return; S.mode = m; saveS(); bandOpts(); showDial(); radioTune(); resetEng(); gen(); slotSep(true); modeView(); }
  function modeView() { CWON = S.mode === 'CW'; root.dataset.m = S.mode === 'CW' ? 'cw' : isDG() ? S.mode.toLowerCase().replace('31', '') : 'ft'; if (S.mode !== 'CW' && TXING && CWTX) cwHalt(); if (DG()) DG().mode(S.mode); fftFit(); wfRange(); drawScale(); }
  function fftFit() { if (AN && AC) { const want = S.mode === 'WSPR' ? 32768 : AC.sampleRate > 30000 ? 8192 : 4096; if (AN.fftSize !== want) AN.fftSize = want; } }
  bandOpts(); showDial();
  document.querySelectorAll('[data-f8m]').forEach(b => b.onclick = () => setMode(b.dataset.f8m));
  $('f8Band').onchange = () => goBand($('f8Band').value);
  $('f8BandR').addEventListener('click', e => { const b = e.target.closest('[data-f8b]'); if (b) goBand(b.dataset.f8b); });

  /* ---------------- decoder engine ---------------- */
  let ENG = null, engP = null;
  const engine = () => engP || (engP = (window.KPCFT8 ? KPCFT8.load('kpc-ft8.wasm?v=20261017a') : Promise.reject(new Error('kpc-ft8.js missing'))).then(e => (ENG = e)));
  function resetEng() { /* the engine is started fresh for every slot */ }

  /* ---------------- audio ---------------- */
  let AC = null, SRC = null, RXG = null, NODE = null, AN = null, STREAM = null, RUN = false;
  const R12 = 12000, RING = R12 * 40; const ring = new Float32Array(RING); let n12 = 0, t0 = 0, peak = 0;
  /* resampler: windowed-sinc low-pass (5 kHz) + fractional step to 12 kHz */
  let rs = null; const dgb = new Float32Array(16384); let dgn = 0, DGON = false;
  function mkRs(rate) {
    const ratio = rate / R12, taps = Math.max(15, Math.round(12 * ratio) | 1), fc = 5000 / rate, h = new Float32Array(taps), mid = (taps - 1) / 2; let sum = 0;
    for (let i = 0; i < taps; i++) { const x = i - mid, w = 0.42 - 0.5 * Math.cos(2 * Math.PI * i / (taps - 1)) + 0.08 * Math.cos(4 * Math.PI * i / (taps - 1)); h[i] = (x === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * x) / (Math.PI * x)) * w; sum += h[i]; }
    for (let i = 0; i < taps; i++) h[i] /= sum;
    return { ratio, h, hist: new Float32Array(taps), hp: 0, pos: 0, cnt: 0 };
  }
  function pushIn(buf) {
    const r = rs, h = r.h, T = h.length; let pk = 0;
    for (let i = 0; i < buf.length; i++) {
      const v = buf[i]; if (Math.abs(v) > pk) pk = Math.abs(v);
      r.hist[r.hp] = v; r.hp = (r.hp + 1) % T; r.cnt++;
      if (r.cnt >= r.pos) { let a = 0, j = r.hp; for (let k = 0; k < T; k++) { a += h[k] * r.hist[j]; j = (j + 1) % T; } ring[n12 % RING] = a; n12++; r.pos += r.ratio; if (CWON) cwFeed(a); else if (DGON && dgn < dgb.length) dgb[dgn++] = a; }
    }
    if (r.cnt > 1e9) { r.cnt -= 1e8; r.pos -= 1e8; }
    peak = Math.max(peak * 0.9, pk);
    /* time of each 12 kHz sample: anchored to the clock, nudged slowly so it never jumps */
    const est = nowS() - n12 / R12 - 0.03; if (!t0 || Math.abs(est - t0) > 1) t0 = est; else t0 += (est - t0) * 0.02;
    if (dgn) { const d = DG(); if (d) d.feed(dgb.subarray(0, dgn), t0 + (n12 - dgn) / R12); dgn = 0; }
    tick();
  }
  const WK = `class K extends AudioWorkletProcessor{constructor(){super();this.b=new Float32Array(2048);this.n=0}process(i){const c=i[0]&&i[0][0];if(c){for(let k=0;k<c.length;k++){this.b[this.n++]=c[k];if(this.n===2048){this.port.postMessage(this.b.slice(0));this.n=0}}}return true}}registerProcessor('kpc-ft8-in',K)`;
  async function startAudio() {
    if (RUN) return true;
    try {
      await engine();
    } catch (e) { note('⚠️ Could not load the FT8 engine: ' + (e.message || e) + '. Reload with signal once.', 6000); return false; }
    try {
      STREAM = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: S.inDev ? { exact: S.inDev } : undefined, echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 } });
    } catch (e) {
      if (S.inDev) { S.inDev = ''; saveS(); return startAudio(); }
      note('⚠️ No audio: ' + (e.message || e) + '. Allow the microphone (that is how the radio audio comes in).', 7000); return false;
    }
    AC = AC || new (window.AudioContext || window.webkitAudioContext)({ latencyHint: 'interactive' }); await AC.resume();
    if (S.outDev && AC.setSinkId) { try { await AC.setSinkId(S.outDev); } catch (e) {} }
    rs = mkRs(AC.sampleRate); n12 = 0; t0 = 0;
    SRC = AC.createMediaStreamSource(STREAM);
    RXG = AC.createGain(); RXG.gain.value = Math.pow(10, (+S.rxg || 0) / 20); SRC.connect(RXG);
    AN = AC.createAnalyser(); AN.fftSize = AC.sampleRate > 30000 ? 8192 : 4096; AN.smoothingTimeConstant = 0; RXG.connect(AN);
    try {
      await AC.audioWorklet.addModule(URL.createObjectURL(new Blob([WK], { type: 'text/javascript' })));
      NODE = new AudioWorkletNode(AC, 'kpc-ft8-in'); NODE.port.onmessage = e => pushIn(e.data);
      const mute = AC.createGain(); mute.gain.value = 0; RXG.connect(NODE); NODE.connect(mute); mute.connect(AC.destination);
    } catch (e) {
      NODE = AC.createScriptProcessor(4096, 1, 1); NODE.onaudioprocess = ev => pushIn(ev.inputBuffer.getChannelData(0).slice(0));
      const mute = AC.createGain(); mute.gain.value = 0; RXG.connect(NODE); NODE.connect(mute); mute.connect(AC.destination);
    }
    fftFit(); RUN = true; $('f8StartBox').hidden = true; root.classList.add('run'); stat(); slotSep(true); wfLoop(); tabDot();
    /* Oct 18 (Brandon's tablet + FT-710: 'in and out are default'): names only show after the first allow, so list again now and pick the radio's USB sound by itself */
    const L = await devices(); if (!S.inDev && !S.mic && L) { const u = L.find(x => x.kind === 'audioinput' && USBRE.test(x.label)); if (u && !TXING) { S.inDev = u.deviceId; saveS(); note('🎧 Using ' + u.label + ' (change it in ⚙ settings).', 4000); stopAudio(); return startAudio(); } }
    clearTimeout(quietT); quietT = setTimeout(() => { if (RUN && peak < 0.0008) note('⚠️ No sound coming in from the radio. Pick the radio under RADIO AUDIO IN (⚙ settings), and check the radio sends audio out its USB (Yaesu menu: USB OUT LEVEL / DATA OUT LEVEL about 50).', 9000); }, 6000);
    return true;
  }
  function stopAudio() {
    RUN = false; try { STREAM && STREAM.getTracks().forEach(t => t.stop()); } catch (e) {} try { NODE && NODE.disconnect(); SRC && SRC.disconnect(); RXG && RXG.disconnect(); } catch (e) {}
    STREAM = SRC = NODE = null; $('f8StartBox').hidden = false; root.classList.remove('run'); stat(); tabDot();
  }
  /* Oct 18 (Brandon: FT-710 gets 1-10 W from the tablet, full power from the laptop): while the mic is open, Android puts the
     whole phone in 'call' mode, so sound out goes through the phone-call path (call volume, call processing).
     On Android we let go of the mic while sending and take it back right after. */
  const ANDR = /Android/i.test(navigator.userAgent);
  let micOff = false;
  function txMicOff() { if (!ANDR || S.txMic !== 'free' || !STREAM || micOff) return; micOff = true; /* Oct 18: made things worse on Brandon's tablet (0 W), so it is off unless S.txMic = 'free' */
    try { SRC && SRC.disconnect(); } catch (e) {} try { STREAM.getTracks().forEach(t => t.stop()); } catch (e) {} SRC = null; STREAM = null; }
  async function txMicOn() { if (!micOff) return; micOff = false; if (!RUN || !AC) return;
    try { STREAM = await navigator.mediaDevices.getUserMedia({ audio: { deviceId: S.inDev ? { exact: S.inDev } : undefined, echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 } });
      SRC = AC.createMediaStreamSource(STREAM); SRC.connect(RXG); } catch (e) { note('⚠️ Could not take the radio audio back after sending: ' + (e.message || e) + '. Press START again.', 6000); stopAudio(); } }
  const USBRE = /usb|codec|digirig|cm1\d\d|pcm29|ft-?\d|ftdx|ic-?\d|yaesu|icom|kenwood|elecraft|signalink|rigblaster|qdx|qmx|trusdx|xiegu/i;
  let quietT = 0;
  async function devices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return null;
    const d = await navigator.mediaDevices.enumerateDevices();
    const opt = (k, sel) => d.filter(x => x.kind === k).map((x, i) => `<option value="${esc(x.deviceId)}"${x.deviceId === sel ? ' selected' : ''}>${esc(x.label || (k === 'audioinput' ? 'Input ' : 'Output ') + (i + 1))}</option>`).join('');
    $('f8In').innerHTML = $('f8In0').innerHTML = '<option value="">Default input</option>' + opt('audioinput', S.inDev);
    const outs = opt('audiooutput', S.outDev);
    $('f8Out').innerHTML = '<option value="">Default output</option>' + outs;
    const can = AC ? !!AC.setSinkId : !!(window.AudioContext && AudioContext.prototype.setSinkId);
    $('f8Out').disabled = !can; $('f8OutT').textContent = can ? '' : 'This browser always plays through the default output. Android and iPhone send it to the radio\'s USB sound by themselves while it is plugged in.';
    return d;
  }
  devices(); if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) navigator.mediaDevices.addEventListener('devicechange', () => devices());
  $('f8In0').onchange = async () => { S.inDev = $('f8In0').value; S.mic = false; saveS(); $('f8In').value = S.inDev; };
  $('f8In').onchange = async () => { S.inDev = $('f8In').value; S.mic = false; saveS(); if (RUN) { stopAudio(); await startAudio(); } };
  $('f8Out').onchange = async () => { S.outDev = $('f8Out').value; saveS(); if (AC && AC.setSinkId) { try { await AC.setSinkId(S.outDev); } catch (e) { note('Could not use that output.'); } } };
  $('f8Start').onclick = startAudio;

  /* ---------------- waterfall ---------------- */
  const wf = $('f8Wf'), sc = $('f8Scale'); let wfRow = null, lastSlotLine = 0;
  let F0 = 100, F1 = 3100;
  function wfRange() { DGON = isDG(); if (S.mode === 'CW') { F0 = 200; F1 = 1400; } else if (isDG() && DG()) { [F0, F1] = DG().range(); } else { F0 = 100; F1 = 3100; } }
  function wfSize() { const w = Math.max(300, Math.round(wf.clientWidth || 600)); if (wf.width !== w) { wf.width = w; sc.width = w; drawScale(); } }
  const hzToX = hz => (hz - F0) / (F1 - F0) * wf.width;
  const xToHz = x => Math.round(F0 + x / wf.width * (F1 - F0));
  function drawScale() {
    const g = sc.getContext('2d'); g.clearRect(0, 0, sc.width, sc.height); g.fillStyle = '#0b0805'; g.fillRect(0, 0, sc.width, sc.height);
    g.fillStyle = '#c9b48a'; g.font = '10px monospace'; g.strokeStyle = '#6b5a3a';
    for (let hz = Math.ceil(F0 / (F1 - F0 > 1500 ? 500 : 200)) * (F1 - F0 > 1500 ? 500 : 200); hz < F1; hz += F1 - F0 > 1500 ? 500 : 200) { if (hz <= F0) continue; const x = hzToX(hz); g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 5); g.stroke(); g.fillText(String(hz), x - 12, 15); }
    const mark = (hz, c, w) => { const x = hzToX(hz), bw = (S.mode === 'FT4' ? 83 : 50) / (F1 - F0) * sc.width; g.fillStyle = c; g.fillRect(x, 0, Math.max(2, bw), w); };
    if (S.mode === 'CW') { const x = hzToX(S.cwHz), bw = cwBwHz() / (F1 - F0) * sc.width; g.fillStyle = '#45e08f'; g.fillRect(x - bw / 2, 0, Math.max(3, bw), 5); return; }
    if (isDG()) { if (DG()) DG().marks((hz, bwHz, c, h) => { const x = hzToX(hz), bw = bwHz / (F1 - F0) * sc.width; g.fillStyle = c; g.fillRect(x - bw / 2, 0, Math.max(2, bw), h || 5); }); return; }
    mark(S.rxHz, '#45e08f', 4); mark(S.txHz, '#ff5c5c', 3);
  }
  const COL = v => { v = Math.max(0, Math.min(1, v)); const r = v < .5 ? 0 : Math.round((v - .5) * 2 * 255), gg = v < .5 ? Math.round(v * 2 * 200) : 200 + Math.round((v - .5) * 110), b = v < .5 ? 90 + Math.round(v * 2 * 120) : Math.round(210 * (1 - (v - .5) * 2)); return [r, Math.min(255, gg), b]; };
  let wfT = 0;
  function wfLoop() {
    if (!RUN) return; requestAnimationFrame(wfLoop);
    const t = performance.now(); if (t - wfT < (S.mode === 'FT4' ? 60 : S.mode === 'CW' ? 50 : S.mode === 'WSPR' ? 500 : isDG() ? 70 : 120) || document.hidden || root.hidden) return; wfT = t;
    wfSize(); const g = wf.getContext('2d'), W = wf.width, H = wf.height;
    const n = AN.frequencyBinCount, d = new Float32Array(n); AN.getFloatFrequencyData(d);
    const binHz = AC.sampleRate / AN.fftSize, row = g.createImageData(W, 1), vals = new Float32Array(W);
    for (let x = 0; x < W; x++) { const hz = xToHz(x), b = Math.min(n - 1, Math.round(hz / binHz)); vals[x] = d[b]; }
    const sorted = Array.from(vals).sort((a, b) => a - b), med = sorted[Math.floor(W * 0.4)] || -100;
    for (let x = 0; x < W; x++) { const [r, gg, b] = COL((vals[x] - med + 2) / 26); row.data[x * 4] = r; row.data[x * 4 + 1] = gg; row.data[x * 4 + 2] = b; row.data[x * 4 + 3] = 255; }
    g.drawImage(wf, 0, 0, W, H - 1, 0, 1, W, H - 1); g.putImageData(row, 0, 0);
    lastVals = vals; if (S.mode === 'CW') { cwWf(vals); } else if (isDG() && DG()) DG().wf(vals); const sl = Math.floor(nowS() / slotLen()); if (isFT() && sl !== lastSlotLine) { lastSlotLine = sl; g.fillStyle = 'rgba(240,201,107,.75)'; g.fillRect(0, 0, W, 1); g.font = '10px monospace'; g.fillText(utc(sl * slotLen(), true), 4, 11); }
    /* level meter (dB above full-scale silence) */
    const db = peak > 0 ? 20 * Math.log10(peak) + 90 : 0; $('f8Lvl').style.width = Math.max(0, Math.min(100, db)) + '%'; $('f8Lvl').className = db < 20 || db > 80 ? 'bad' : '';
    $('f8LvlT').textContent = Math.round(db) + ' dB ' + (db < 20 ? '(too low: turn the radio\'s audio up)' : db > 80 ? '(too high: turn RX GAIN down in ⚙ settings)' : '(good)');
  }
  wf.addEventListener('click', e => { const r = wf.getBoundingClientRect(), hz = xToHz((e.clientX - r.left) * wf.width / r.width);
    if (S.mode === 'CW') { cwPitch(snapPeak(hz)); return; }
    if (isDG()) { if (DG()) DG().click(hz, e.shiftKey); return; }
    if (e.shiftKey) S.txHz = hz; else { S.rxHz = hz; if (!S.hold) S.txHz = hz; } saveS(); hzBoxes(); drawScale(); drawRx(); });
  wf.addEventListener('contextmenu', e => { e.preventDefault(); if (!isFT()) return; const r = wf.getBoundingClientRect(); S.txHz = xToHz((e.clientX - r.left) * wf.width / r.width); saveS(); hzBoxes(); drawScale(); });
  addEventListener('resize', () => { if (!root.hidden) wfSize(); });

  /* ---------------- CW: decoder + keyboard (Brandon Oct 17: 'cw decode and cw keyboard to cw') ----------------
     Decoder: the 12 kHz audio is mixed down at the pitch, run through a 3-stage low-pass (the CW filter), and the envelope is
     checked every 2 ms against a moving noise floor; mark / space lengths are timed against a learned dit length. */
  const MORSE = { '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F', '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L', '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R', '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X', '-.--': 'Y', '--..': 'Z',
    '-----': '0', '.----': '1', '..---': '2', '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7', '---..': '8', '----.': '9', '..--..': '?', '-..-.': '/', '.-.-.-': '.', '--..--': ',', '-...-': '=', '.-.-.': '+', '-....-': '-', '...-.-': '<SK>', '-.--.': '<KN>', '.-...': '<AS>' };
  const TOM = {}; Object.entries(MORSE).forEach(([k, v]) => { if (v.length === 1) TOM[v] = k; });
  let CWON = false, CWTX = false;
  const C = { ph: 0, a: [0, 0, 0, 0, 0, 0], n: 0, env: 0, sig: 1e-6, flo: 1e-6, on: false, run: 0, mk: 0, sp: 0, dit: 60, cur: '', txt: '', spaced: true, snr: 0 };
  const cwBwHz = () => S.cwBw === 'auto' ? Math.max(50, Math.min(160, 2.6 * 1200 / C.dit)) : +S.cwBw;
  function cwFeed(v) {
    const w = 2 * Math.PI * S.cwHz / R12; C.ph += w; if (C.ph > 6.283185307) C.ph -= 6.283185307;
    let i = v * Math.cos(C.ph), q = v * Math.sin(C.ph); const fa = 1 - Math.exp(-2 * Math.PI * (cwBwHz() / 2 / 0.51) / R12), A = C.a;
    A[0] += fa * (i - A[0]); A[1] += fa * (A[0] - A[1]); A[2] += fa * (A[1] - A[2]); A[3] += fa * (q - A[3]); A[4] += fa * (A[3] - A[4]); A[5] += fa * (A[4] - A[5]);
    if (++C.n < 24) return; C.n = 0; /* every 2 ms */
    const e = Math.sqrt(A[2] * A[2] + A[5] * A[5]); C.env = C.env * .6 + e * .4;
    C.sig = Math.max(C.env, C.sig * 0.9995); C.flo = C.env < C.flo ? C.flo * .97 + C.env * .03 : C.flo * 1.0008 + 1e-9;
    if (C.flo > C.sig * .6) C.flo = C.sig * .6;
    const thHi = C.flo + (C.sig - C.flo) * .5, thLo = C.flo + (C.sig - C.flo) * .35, snr = C.sig / (C.flo || 1e-9);
    C.snr = snr; const usable = snr > 2.2;
    const now = C.on ? C.env > thLo : C.env > thHi;
    if (now !== C.on) { if (++C.run < 3) { cwTime(); return; } C.run = 0;
      if (C.on) { const d = C.mk; if (usable) cwMark(d); } C.on = now; C.mk = 0; C.sp = 0; }
    else C.run = 0;
    cwTime();
  }
  function cwTime() { if (C.on) C.mk += 2; else { C.sp += 2; const dit = C.dit;
    if (C.cur && C.sp > 2.4 * dit) { cwChar(MORSE[C.cur] || (C.cur.length > 7 ? '' : '*')); C.cur = ''; }
    if (!C.spaced && C.sp > 5.5 * dit) { cwChar(' '); C.spaced = true; } } }
  function cwMark(d) { if (d < 12) return; const dit = C.dit;
    if (d < 2 * dit) { C.cur += '.'; C.dit = Math.max(20, Math.min(240, dit * .8 + d * .2)); } else { C.cur += '-'; C.dit = Math.max(20, Math.min(240, dit * .85 + d / 3 * .15)); }
    C.spaced = false; if (C.cur.length > 8) C.cur = ''; }
  let cwBuf = '', cwDrawT = null;
  function cwChar(ch) { if (ch === ' ' && / $/.test(C.txt)) return; C.txt = (C.txt + ch).slice(-4000); clearTimeout(cwDrawT); cwDrawT = setTimeout(cwDraw, 60); }
  const CALLRE = /\b((?:[A-Z]{1,2}\d?\/)?[A-Z]{1,2}\d[A-Z]{1,4}(?:\/[A-Z0-9]{1,3})?)\b/g;
  function cwDraw() {
    const el = $('cwRx'), stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 20;
    el.innerHTML = esc(C.txt).replace(/&lt;(SK|KN|AS)&gt;/g, '<i>$1</i>') + '<span class="cw-cur">' + (C.cur ? esc(C.cur) : '▌') + '</span>';
    if (stick) el.scrollTop = el.scrollHeight;
    /* call signs heard: tap one to put it in THEIR CALL */
    const me = myCall(), seen = []; let m; CALLRE.lastIndex = 0; const tail = C.txt.slice(-600);
    while ((m = CALLRE.exec(tail))) { const c = m[1]; if (c !== me && !seen.includes(c) && /\d/.test(c) && c.length >= 4) seen.push(c); }
    $('cwCalls').innerHTML = seen.slice(-8).reverse().map(c => { const sp = spotRef(c); return `<button type="button" data-cwc="${esc(c)}" class="${sp ? 'park' : ''}">${esc(c)}${sp ? ' 🌲 ' + esc(sp.reference) : ''}</button>`; }).join('');
    $('cwWpmT').textContent = Math.round(1200 / C.dit); $('cwSnT').textContent = C.snr > 2.2 ? (C.snr > 6 ? 'GOOD' : 'WEAK') : 'TOO WEAK';
  }
  function cwPitch(hz) { S.cwHz = Math.max(250, Math.min(1300, Math.round(hz))); saveS(); $('cwHzT').textContent = S.cwHz; C.sig = 1e-6; C.flo = 1e-6; C.cur = ''; drawScale(); }
  /* waterfall helpers: snap a tap to the nearest peak; AFC follows the strongest trace */
  let lastVals = null;
  function cwWf(vals) { lastVals = vals; if ($('cwAfc').checked && !CWTX) { const pk = peakIn(F0 + 50, F1 - 50); if (pk && Math.abs(pk - S.cwHz) > 25) { cwAfcN = (cwAfcN || 0) + 1; if (cwAfcN > 8) { cwPitch(pk); cwAfcN = 0; } } else cwAfcN = 0; } }
  let cwAfcN = 0;
  function peakIn(a, b) { if (!lastVals) return 0; let best = -1e9, bx = -1; const x0 = Math.max(0, Math.round(hzToX(a))), x1 = Math.min(lastVals.length - 1, Math.round(hzToX(b)));
    for (let x = x0; x <= x1; x++) if (lastVals[x] > best) { best = lastVals[x]; bx = x; } const sorted = Array.from(lastVals).sort((p, q) => p - q), med = sorted[Math.floor(sorted.length / 2)];
    return bx >= 0 && best - med > 8 ? xToHz(bx) : 0; }
  function snapPeak(hz) { const pk = peakIn(hz - 40, hz + 40); return pk || hz; }
  /* sending */
  const MAC0 = h => [['CQ', h ? 'CQ CQ DE {MY} {MY} K' : 'CQ POTA DE {MY} {MY} K'], ['CALL', '{MY}'], ['REPORT', '{THEIR} TU 5NN {ST} {ST} BK'], ['TU', 'TU 73 DE {MY}'], ['QRZ', 'QRZ? DE {MY}'], ['AGN', 'AGN?'], ['P2P', '{THEIR} TU 5NN P2P {REF} BK'], ['73', '73 TU EE']];
  function macros() { const L = LG(), hunt = L ? L.me().hunt : false; return S.cwMac || MAC0(hunt); }
  function fill(t) { const L = LG(), me = L ? L.me() : {}; return String(t).replace(/\{MY\}/g, myCall() || 'K4TEST').replace(/\{THEIR\}/g, $('cwCall').value.trim().toUpperCase() || '').replace(/\{REF\}/g, (me.pota && me.pota[0]) || '').replace(/\{ST\}/g, stateOf(myGrid()) || '').replace(/\s+/g, ' ').trim(); }
  function macDraw() { $('cwMac').innerHTML = macros().map((m, i) => `<button type="button" data-mac="${i}" title="${esc(m[1])}">F${i + 1} ${esc(m[0])}</button>`).join('') + '<button type="button" data-macedit>✏️ EDIT</button>'; }
  function elems(t, wpm) { const u = 1200 / wpm, out = []; for (const w of t.split(' ')) { if (out.length) out.push([0, 4 * u]); [...w].forEach((ch, i) => { const k = TOM[ch]; if (!k) return; if (i) out.push([0, 2 * u]); [...k].forEach((e, j) => { if (j) out.push([0, u]); out.push([1, e === '.' ? u : 3 * u]); }); out.push([0, u]); }); } return out; }
  let cwStopFlag = false;
  /* Oct 17 (Brandon: 'will it make cw short hand if I type it out?'): optional, off by default */
  const CWAB = [['THANK YOU VERY MUCH', 'TNX FER'], ['THANK YOU', 'TU'], ['THANKS', 'TNX'], ['PLEASE', 'PSE'], ['YOUR', 'UR'], ['YOU ARE', 'UR'], ['YOU', 'U'], ['ARE', 'R'], ['GOOD MORNING', 'GM'], ['GOOD AFTERNOON', 'GA'], ['GOOD EVENING', 'GE'], ['GOOD NIGHT', 'GN'],
    ['NAME IS', 'NAME'], ['MY NAME', 'NAME'], ['REPORT', 'RPT'], ['SIGNAL', 'SIG'], ['WEATHER', 'WX'], ['ANTENNA', 'ANT'], ['RADIO', 'RIG'], ['AGAIN', 'AGN'], ['ROGER', 'R'], ['FOR', 'FER'], ['AND', 'ES'], ['BEST REGARDS', '73'], ['REGARDS', '73'], ['GOODBYE', '73'], ['BYE', '73'],
    ['THE', ''], ['POWER', 'PWR'], ['WATTS', 'W'], ['HERE', 'HR'], ['THERE', 'THR'], ['VERY', 'VY'], ['GOOD', 'GUD'], ['NICE', 'NICE'], ['STATE', 'ST'], ['PARK', 'PARK'], ['NUMBER', 'NR'], ['QUESTION', '?'], ['OLD MAN', 'OM'], ['FINE BUSINESS', 'FB'], ['WORKED', 'WKD'], ['ABOUT', 'ABT'], ['AFTER', 'AFTR'], ['BEFORE', 'B4'], ['COPY', 'CPY'], ['RECEIVED', 'RCVD'], ['LISTENING', 'QRL?']];
  function cwShort(t) { let x = ' ' + t.replace(/\s+/g, ' ') + ' '; for (const [a, b] of CWAB) x = x.split(' ' + a + ' ').join(b ? ' ' + b + ' ' : ' '); return x.replace(/\s+/g, ' ').trim(); }
  async function cwSendText(t) {
    t = fill(t).toUpperCase(); if (S.cwAbbr) t = cwShort(t); if (!t) return; if (!myCall()) { note('Put YOUR call in ⚙ STATION first: nothing was sent.', 4000); return; }
    if (CWTX) { note('Still sending: wait or press STOP.', 2000); return; }
    CWTX = true; TXING = true; stat(); cwStopFlag = false; const wpm = +S.cwWpm || 20, via = S.cwVia;
    $('cwSending').textContent = '▶ ' + t; C.txt += '\n[TX] ' + t + '\n'; cwDraw();
    try {
      if (via === 'cat') { if (!window.KPCCat || !KPCCat.connected() || !KPCCat.cwCan()) { note('Radio keyer not available: connect the radio (CAT), or pick a key line / audio in SEND WITH.', 5000); return; }
        await KPCCat.cw(t, wpm); await new Promise(r => setTimeout(r, elems(t, wpm).reduce((a, e) => a + e[1], 0) + 200)); }
      else if (via === 'dtr' || via === 'rts') { if (!window.KPCCat || !(await KPCCat.connect(false))) { note('Connect the radio / cable first (📻 CONNECT MY RADIO in ⚙ SETTINGS).', 5000); return; }
        let t1 = performance.now(); for (const [k, d] of elems(t, wpm)) { if (cwStopFlag) break; await KPCCat.keyLine(!!k, via); t1 += d; const w = t1 - performance.now(); if (w > 0) await new Promise(r => setTimeout(r, w)); } await KPCCat.keyLine(false, via); }
      else { if (!AC) { await startAudio(); if (!AC) return; } const rate = AC.sampleRate, E = elems(t, wpm), tot = E.reduce((a, e) => a + e[1], 0) / 1000, buf = AC.createBuffer(1, Math.ceil((tot + .1) * rate), rate), d = buf.getChannelData(0), rise = Math.round(.005 * rate);
        let n = 0; for (const [k, ms] of E) { const len = Math.round(ms / 1000 * rate); if (k) for (let i = 0; i < len; i++) { const env = Math.min(1, i / rise, (len - i) / rise); d[n + i] = Math.sin(2 * Math.PI * (S.cwTone || S.cwHz) * (n + i) / rate) * env; } n += len; }
        const g = AC.createGain(); g.gain.value = S.lvl; (window.__kpcTxG = (window.__kpcTxG || []).filter(x => x.context === g.context).slice(-6)).push(g); const src = AC.createBufferSource(); src.buffer = buf; src.connect(g); g.connect(AC.destination); TXSRC = src;
        await ptt(true); await new Promise(r => { src.onended = r; src.start(AC.currentTime + .08); }); await ptt(false); TXSRC = null; }
    } finally { CWTX = false; TXING = false; stat(); $('cwSending').textContent = ''; }
  }
  function cwHalt() { cwStopFlag = true; try { TXSRC && TXSRC.stop(); } catch (e) {} if (window.KPCCat) { KPCCat.cwStop(); if (S.cwVia === 'dtr' || S.cwVia === 'rts') KPCCat.keyLine(false, S.cwVia); } ptt(false); }
  function cwInit() {
    $('cwHzT').textContent = S.cwHz; $('cwWpm').value = S.cwWpm; $('cwVia').value = S.cwVia; $('cwBw').value = S.cwBw;
    $('cwWpm').onchange = () => { S.cwWpm = Math.max(8, Math.min(45, +$('cwWpm').value || 20)); saveS(); };
    $('cwTone').value = S.cwTone || ''; $('cwTone').onchange = () => { const v = +$('cwTone').value; S.cwTone = v ? Math.max(300, Math.min(1200, v)) : 0; $('cwTone').value = S.cwTone || ''; saveS(); };
    $('cwAbbr').checked = !!S.cwAbbr; $('cwAbbr').onchange = () => { S.cwAbbr = $('cwAbbr').checked; saveS(); };
    $('cwVia').onchange = () => { S.cwVia = $('cwVia').value; saveS(); };
    $('cwBw').onchange = () => { S.cwBw = $('cwBw').value; saveS(); drawScale(); };
    $('cwClr').onclick = () => { C.txt = ''; cwDraw(); };
    $('cwTx').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); const v = $('cwTx').value; $('cwTx').value = ''; cwSendText(v); } });
    $('cwSend').onclick = () => { const v = $('cwTx').value; $('cwTx').value = ''; cwSendText(v); };
    $('cwStop').onclick = cwHalt;
    $('cwMac').addEventListener('click', e => { const b = e.target.closest('[data-mac]'); if (b) { cwSendText(macros()[+b.dataset.mac][1]); return; }
      if (e.target.closest('[data-macedit]')) { const M = macros().map(m => m.slice()); for (let i = 0; i < M.length; i++) { const v = prompt(`F${i + 1} ${M[i][0]} (use {MY} {THEIR} {REF} {ST}; blank = keep, RESET = defaults)`, M[i][1]); if (v === null) break; if (v.trim().toUpperCase() === 'RESET') { S.cwMac = null; saveS(); macDraw(); return; } if (v.trim()) M[i][1] = v.trim().toUpperCase(); } S.cwMac = M; saveS(); macDraw(); } });
    addEventListener('keydown', e => { if (root.hidden || S.mode !== 'CW' || !/^F[1-8]$/.test(e.key)) return; e.preventDefault(); const m = macros()[+e.key.slice(1) - 1]; if (m) cwSendText(m[1]); });
    $('cwCalls').addEventListener('click', e => { const b = e.target.closest('[data-cwc]'); if (!b) return; $('cwCall').value = b.dataset.cwc; const sp = spotRef(b.dataset.cwc); if (sp) $('cwRef').value = sp.reference; });
    $('cwCall').oninput = e => { e.target.value = e.target.value.toUpperCase().replace(/\s/g, ''); };
    $('cwLog').onclick = () => { const L = LG(), call = $('cwCall').value.trim().toUpperCase(); if (!L || !call) { note('Type or tap their call first.'); return; }
      const k = (!(S.ov && S.ov[ovKey()]) && L.freq && L.freq() && L.band(L.freq()) === S.band) ? L.freq() : dialK();
      const r = L.add({ call, khz: k, mode: 'CW', rs: $('cwRs').value || '599', rr: $('cwRr').value || '599', ref: $('cwRef').value.trim() });
      if (r && r.ok) { note(`✅ ${call} logged · ${S.band} CW${r.n ? ' · ' + r.n + (L.me().hunt ? ' today' : ' this activation') : ''}`, 3000, 'log'); $('cwCall').value = ''; $('cwRef').value = ''; } else note('⚠️ Not logged: ' + ((r && r.msg) || ''), 5000); };
    macDraw(); setInterval(() => { if (CWON && !root.hidden) cwDraw(); }, 1000);
  }

  /* ---------------- grids, distance, states (GridTracker ideas, Brandon Oct 17: map, alerts, who hears me, distance) ---------------- */
  function g2ll(g) { g = String(g || '').toUpperCase(); if (!/^[A-R]{2}\d{2}/.test(g)) return null; let lo = (g.charCodeAt(0) - 65) * 20 - 180 + (+g[2]) * 2, la = (g.charCodeAt(1) - 65) * 10 - 90 + (+g[3]);
    if (/^[A-R]{2}\d{2}[A-X]{2}/.test(g)) { lo += (g.charCodeAt(4) - 65) / 12 + 1 / 24; la += (g.charCodeAt(5) - 65) / 24 + 1 / 48; } else { lo += 1; la += 0.5; } return [la, lo]; }
  const RAD = Math.PI / 180, CMP = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  function distB(a, b) { const dl = (b[0] - a[0]) * RAD, dn = (b[1] - a[1]) * RAD, x = Math.sin(dl / 2) ** 2 + Math.cos(a[0] * RAD) * Math.cos(b[0] * RAD) * Math.sin(dn / 2) ** 2, mi = 2 * 3958.8 * Math.asin(Math.sqrt(x));
    const y = Math.sin(dn) * Math.cos(b[0] * RAD), z = Math.cos(a[0] * RAD) * Math.sin(b[0] * RAD) - Math.sin(a[0] * RAD) * Math.cos(b[0] * RAD) * Math.cos(dn), br = (Math.atan2(y, z) / RAD + 360) % 360;
    return { mi: Math.round(mi), br: Math.round(br), c: CMP[Math.round(br / 45) % 8] }; }
  const GRIDS = get('kpcFt8Grids', {}); /* call → grid, remembered so later lines (reports, RR73) show distance too */
  let gridSave = null; const gridOf = c => GRIDS[c] || '';
  function myLL() { return g2ll(myGrid()); }
  let STATES = null; fetch('kpc-us-states.json').then(r => r.json()).then(j => { STATES = j; }).catch(() => {});
  function inRing(pt, r) { let c = false; for (let i = 0, j = r.length - 1; i < r.length; j = i++) { const [xi, yi] = r[i], [xj, yj] = r[j]; if (((yi > pt[1]) !== (yj > pt[1])) && pt[0] < (xj - xi) * (pt[1] - yi) / (yj - yi) + xi) c = !c; } return c; }
  function stateOf(g) { const ll = g2ll(g); if (!ll || !STATES) return ''; const pt = [ll[1], ll[0]]; for (const s0 of STATES) for (const poly of s0.p) if (inRing(pt, poly[0])) return s0.a; return ''; }
  function workedSets() { const L = LG(), Q = L && L.qs ? L.qs() : []; const st = new Set(), gr = new Set(); for (const q of Q) { if (q.st) st.add(String(q.st).toUpperCase()); if (q.g) gr.add(String(q.g).slice(0, 4).toUpperCase()); } return { st, gr }; }

  /* alerts: a soft two-note chime + a note, once per call every 10 minutes */
  const ALS = {};
  function chime() { try { if (!AC) return; const t = AC.currentTime; [880, 1320].forEach((f, i) => { const o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = f; g.gain.setValueAtTime(0.0001, t + i * .16); g.gain.exponentialRampToValueAtTime(.18, t + i * .16 + .02); g.gain.exponentialRampToValueAtTime(.0001, t + i * .16 + .25); o.connect(g); g.connect(AC.destination); o.start(t + i * .16); o.stop(t + i * .16 + .3); }); } catch (e) {} }
  function alerts(sl) {
    if (TXING) return; const now = nowS(), W = workedSets(), watch = String(S.watch || '').toUpperCase().split(/[\s,;]+/).filter(Boolean), hits = [];
    for (const x of LINES) { if (x.sl !== sl || !x.fr || /\.\.\./.test(x.fr) || x.me) continue;
      let why = '';
      if (watch.includes(x.fr)) why = '👀 ' + x.fr + ' is on the air';
      else if (S.aPark && x.cq) { const sp = spotRef(x.fr); if (sp || /^(POTA|SOTA|WWFF)$/.test(x.cqw)) { const L0 = LG(), nw = sp && L0 && L0.newPark && L0.newPark(sp.reference); why = (nw ? '🆕 NEW PARK: ' : '🌲 ') + x.fr + ' calling CQ' + (sp ? ' from ' + sp.reference : ' ' + x.cqw); } }
      if (!why && x.cq && x.grid) { const st = stateOf(x.grid); if (S.aState && st && !W.st.has(st)) why = '🆕 New state: ' + st + ' (' + x.fr + ')'; else if (S.aGrid && !W.gr.has(x.grid.slice(0, 4))) why = '🆕 New grid: ' + x.grid + ' (' + x.fr + ')'; }
      if (why && (!ALS[x.fr] || now - ALS[x.fr] > 600)) { ALS[x.fr] = now; x.al = 1; hits.push(why); } }
    if (hits.length) { chime(); note('🔔 ' + hits.slice(0, 3).join(' · ') + (hits.length > 3 ? ' +' + (hits.length - 3) : '') + ' · tap their line to call', 6000, 'al'); }
  }

  /* ---------------- decodes ---------------- */
  let LINES = [], lastDecSlot = -1, txSlots = new Set(), dtAvg = [];
  const MAXL = 400;
  function slotSep(force) { const sl = Math.floor(nowS() / slotLen()); if (force || !LINES.length || LINES[LINES.length - 1].sep !== sl) { /* separators come with each decode */ } }
  function tick() {
    if (!isFT()) return;
    const t = nowS(), L = slotLen(), sl = Math.floor(t / L), into = t - sl * L;
    $('f8SlotBar').style.width = (into / L * 100) + '%';
    /* decode the slot that just ended (FT8 at 14.4 s, FT4 at 6.6 s into the slot) */
    const at = S.mode === 'FT4' ? 6.6 : 14.4;
    if (RUN && into >= at && lastDecSlot !== sl) { lastDecSlot = sl; decodeSlot(sl); }
    txTick(t, sl, into);
  }
  setInterval(() => { $('f8Utc').textContent = utc(nowS(), true).replace(/(\d\d)(\d\d)(\d\d)/, '$1:$2:$3'); if (!RUN) { const t = nowS(), L = slotLen(); $('f8SlotBar').style.width = ((t % L) / L * 100) + '%'; } else if (!NODE || !NODE.port) tick(); }, 250);
  function decodeSlot(sl) {
    if (!ENG) return; const L = slotLen(), start = sl * L;
    if (txSlots.has(S.mode + sl)) return; /* we were sending */
    const i0 = Math.round((start - t0) * R12), want = Math.round(L * R12);
    if (i0 < n12 - RING || i0 + want * 0.85 > n12) return;
    const buf = new Float32Array(want); for (let i = 0; i < want; i++) { const j = i0 + i; buf[i] = j >= 0 && j < n12 ? ring[((j % RING) + RING) % RING] : 0; }
    let D = [];
    try { ENG.start(S.mode === 'FT4'); ENG.feed(buf); D = ENG.decode(S.deep ? 6 : 10, S.deep ? 40 : 25); } catch (e) { console.error(e); return; }
    const me = myCall(), par = sl % 2;
    D.sort((a, b) => a.hz - b.hz);
    if (D.length) { const dts = D.map(d => d.dt).sort((a, b) => a - b); dtAvg.push(dts[Math.floor(dts.length / 2)]); if (dtAvg.length > 8) dtAvg.shift(); clockHint(); }
    LINES.push({ sep: sl, t: start, mode: S.mode });
    for (const d of D) {
      const tk = d.text.split(/\s+/), to = clean(tk[0]), fr = clean(tk[0] === 'CQ' ? (tk.length > 3 ? tk[2] : tk[1]) : tk[1]);
      LINES.push({ t: start, sl, par, db: d.db, dt: d.dt, hz: d.hz, text: d.text, cq: tk[0] === 'CQ', cqw: tk[0] === 'CQ' && tk.length > 3 ? tk[1] : '', to, fr, me: !!me && to === me, grid: tk.length >= 3 && isGrid(tk[tk.length - 1]) ? tk[tk.length - 1].toUpperCase() : '' });
    }
    if (LINES.length > MAXL) LINES = LINES.slice(-MAXL);
    for (const x of LINES) if (x.sl === sl && x.grid && x.fr && !/\.\.\./.test(x.fr)) GRIDS[x.fr] = x.grid;
    clearTimeout(gridSave); gridSave = setTimeout(() => { const k = Object.keys(GRIDS); if (k.length > 3000) k.slice(0, k.length - 3000).forEach(c => delete GRIDS[c]); put('kpcFt8Grids', GRIDS); }, 2000);
    $('f8Cnt').textContent = D.length + ' decoded';
    alerts(sl); drawBand(); drawRx(); seq(sl, D); mapDraw();
  }
  function clockHint() { if (dtAvg.length < 3) return; const m = dtAvg.slice().sort((a, b) => a - b)[Math.floor(dtAvg.length / 2)]; if (Math.abs(m) > 1) note(`⏱ Most stations show DT ${m > 0 ? '+' : ''}${m.toFixed(1)} s: your clock is about ${Math.abs(m).toFixed(1)} s ${m > 0 ? 'slow' : 'fast'}. Turn on "set time automatically" or FT8 contacts may fail.`, 8000, 'clk'); }
  /* is this station a park activator right now? (on the POTA / WWFF / SOTA spot lists; FT8/FT4 spots first) — Brandon Oct 17: 'highlight other pota stations' */
  const spotRef = call => { const L = LG(); if (!L || !call) return null; const A = (L.spots() || []).filter(x => x.activator === call && x.reference); return A.find(x => /FT8|FT4/i.test(x.mode || '')) || A[0] || null; };
  function lineHtml(x) {
    if (x.sep != null) return `<div class="f8-sep">${utc(x.t, true).replace(/(\d\d)(\d\d)(\d\d)/, '$1:$2:$3')} ── ${x.mode}</div>`;
    const L = LG(), wk = L && x.fr && L.worked(x.fr), sp = x.tx ? null : spotRef(x.fr) || (x.cq ? null : spotRef(x.to)), park = sp || /^(POTA|SOTA|WWFF)$/.test(x.cqw), cls = x.tx ? 'tx' : x.me ? 'me' : x.cq ? (x.cqw ? 'cqp' : 'cq') : '';
    if (S.potaOnly && !park && !x.tx && !x.me) return '';
    return `<div class="f8-l ${cls}${wk ? ' wk' : ''}${park ? ' park' : ''}${x.al ? ' al' : ''}" data-l="${x.id || ''}" role="button" tabindex="0"><span class="tm">${x.tx ? utc(x.t, true) : utc(x.t, true)}</span><span class="db">${x.tx ? 'Tx' : fmtDb(x.db)}</span><span class="dt">${x.tx ? '' : (x.dt >= 0 ? ' ' : '') + x.dt.toFixed(1)}</span><span class="hz">${x.hz}</span><span class="tx">${x.tx ? '~' : '~'}</span><span class="m">${esc(x.text)}${sp ? ` <i class="ref">${sp.prog === 'SOTA' ? '⛰' : sp.prog === 'WWFF' ? '🌳' : '🌲'} ${esc(sp.reference)}${sp.activator !== x.fr ? ' (' + esc(sp.activator) + ')' : ''}${L && L.newPark && (sp.prog || 'POTA') === 'POTA' && L.newPark(sp.reference) ? ' · 🆕 NEW PARK' : ''}</i>` : ''}${wk ? ' <i class="wkd">✓</i>' : ''}${(() => { if (x.tx) return ''; const g = x.grid || gridOf(x.fr), a = myLL(), b = g2ll(g); if (!a || !b) return ''; const d = distB(a, b); return ` <i class="dst" title="${d.br}°">${d.mi.toLocaleString()} mi ${d.c}</i>`; })()}</span></div>`;
  }
  let lid = 0; const byId = {};
  function idOf(x) { if (!x.id) { x.id = ++lid; byId[x.id] = x; } return x.id; }
  function drawBand() { const el = $('f8Band1'), stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 30; const L = LINES.slice(-220); L.forEach(idOf); el.innerHTML = L.map(lineHtml).join(''); if (stick) el.scrollTop = el.scrollHeight; }
  let MYQ = [];
  function drawRx() {
    const el = $('f8Rx'); const w = S.mode === 'FT4' ? 90 : 60, dx = QS.dx;
    const L = LINES.filter(x => x.sep == null && (Math.abs(x.hz - S.rxHz) <= w || x.me || (dx && x.fr === dx))).concat(MYQ).sort((a, b) => a.t - b.t || (a.tx ? 1 : 0) - (b.tx ? 1 : 0)).slice(-80);
    L.forEach(idOf); el.innerHTML = L.map(lineHtml).join('') || '<div class="f8-empty">Stations near your RX frequency and your own contact show here.</div>'; el.scrollTop = el.scrollHeight;
    $('f8RxHz').textContent = S.rxHz + ' Hz';
  }
  function pick(x) {
    if (!x || x.sep != null) return;
    if (x.tx) { const c = clean(String(x.text || '').split(/\s+/)[0]); if (c && c !== 'CQ' && c !== 'DXCALL') { QS.dx = c; $('f8Dx').value = c; gen(); note('📞 ' + c + ' is back in DX CALL.', 2000); } return; }
    const me = myCall(); const other = x.me ? x.fr : (x.cq ? x.fr : (x.fr && x.fr !== me ? x.fr : x.to));
    if (!other || other === '...' || /\.\.\./.test(other)) { note('That call is hidden (a long or odd call sign). Wait for them to send their full call.'); return; }
    const keepG = QS.dx === other ? QS.grid : ''; QS.dx = other; QS.grid = x.grid || keepG; QS.rs = fmtDb(x.db); QS.rr = ''; QS.state = 'call'; QS.logged = false; QS.tries = 0; QS.since = nowS(); QS.ref = (spotRef(other) || {}).reference || QS.ref || '';
    S.rxHz = x.hz; if (!S.hold) S.txHz = x.hz; S.even = x.par === 1; saveS();
    $('f8Dx').value = QS.dx; $('f8DxG').value = QS.grid; $('f8Rpt').value = QS.rs;
    gen();
    /* answering them: if they're already calling me, jump ahead like WSJT-X */
    let n = 1; if (x.me) { const tk = x.text.split(/\s+/), last = tk[tk.length - 1]; if (isRpt(last)) { QS.rr = last; n = 3; } else if (isRRpt(last)) { QS.rr = last.slice(1); n = 4; } else if (last === 'RR73' || last === 'RRR') n = 5; else n = 2; }
    QS.cq = false; nextTx(n); txOn(true); hzBoxes(); drawScale(); drawRx(); chk(); note('📞 Calling ' + other + ' (Tx' + n + ')', 2000);
  }
  ['f8Band1', 'f8Rx'].forEach(i => $(i).addEventListener('click', e => { const r = e.target.closest('[data-l]'); if (r) pick(byId[r.dataset.l]); }));
  ['f8Band1', 'f8Rx'].forEach(i => $(i).addEventListener('keydown', e => { if (e.key === 'Enter') { const r = e.target.closest('[data-l]'); if (r) pick(byId[r.dataset.l]); } }));

  /* ---------------- map: who I hear + who hears me ---------------- */
  let MAP = null, ML = null, ME = null, HEARD = {}, mqC = null, mqFor = '', pskT = 0, XH = [], XM = [];
  function mapInit() { if (MAP || !window.L) return; MAP = L.map('f8Map', { worldCopyJump: true, zoomControl: true }).setView(myLL() || [37.8, -85.7], 4);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 12, attribution: 'Esri' }).addTo(MAP);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', { maxZoom: 12 }).addTo(MAP);
    ML = L.layerGroup().addTo(MAP);
    ML.on('click', e => { const id = e.layer && e.layer.options && e.layer.options.lid; if (id && byId[id]) pick(byId[id]); }); }
  function mapDraw() {
    const w = $('f8MapW'); if (!w.open || root.hidden) return; mapInit(); if (!MAP) { $('f8MapT').textContent = 'map needs signal to load'; return; }
    ML.clearLayers(); const me = myLL(), now = nowS(); let n = 0, m = 0;
    if (me) L.marker(me, { icon: L.divIcon({ className: 'f8-star', html: '★', iconSize: [22, 22] }) }).addTo(ML).bindTooltip('You · ' + myGrid());
    if (S.mode === 'WSPR') { /* WSPR: stations I decoded (green) + stations that heard me on wspr.live (orange ▲) */
      if (S.mm !== 'me') for (const x of XH) { const ll = g2ll(x.grid); if (!ll) continue; n++; L.circleMarker(ll, { radius: 5 + Math.max(0, Math.min(6, (x.snr + 30) / 5)), color: '#3ddc84', weight: 1, fillColor: '#3ddc84', fillOpacity: .8 }).addTo(ML).bindTooltip(`${x.call} ${x.snr} dB${me ? ' · ' + distB(me, ll).mi.toLocaleString() + ' mi' : ''}`); }
      if (S.mm !== 'hear') for (const x of XM) { const ll = g2ll(x.grid); if (!ll) continue; m++; L.marker(ll, { icon: L.divIcon({ className: 'f8-tri', html: '▲', iconSize: [16, 16] }) }).addTo(ML).bindTooltip(`${x.call} heard you ${x.snr} dB${me ? ' · ' + distB(me, ll).mi.toLocaleString() + ' mi' : ''}`); }
      $('f8MapT').textContent = (S.mm !== 'me' ? n + ' heard' : '') + (S.mm === 'both' ? ' · ' : '') + (S.mm !== 'hear' ? m + ' heard you (wspr.live)' : ''); return; }
    if (S.mm !== 'me') { const seen = {};
      for (let i = LINES.length - 1; i >= 0; i--) { const x = LINES[i]; if (x.sep != null || x.tx || !x.fr || seen[x.fr] || now - x.t > 1800 || /\.\.\./.test(x.fr)) continue; seen[x.fr] = 1;
        const ll = g2ll(x.grid || gridOf(x.fr)); if (!ll) continue; idOf(x); n++;
        const sp = spotRef(x.fr), col = x.me ? '#ff4d4d' : x.cq ? '#3ddc84' : '#4da3ff', age = Math.min(1, (now - x.t) / 1800);
        L.circleMarker(ll, { radius: 5 + Math.max(0, Math.min(6, (x.db + 20) / 5)), color: sp || x.cqw ? '#fff' : col, weight: sp || x.cqw ? 3 : 1, fillColor: col, fillOpacity: .85 - age * .55, lid: x.id })
          .addTo(ML).bindTooltip(`${x.fr} ${fmtDb(x.db)}${sp ? ' · 🌲 ' + sp.reference : ''}${me ? ' · ' + distB(me, ll).mi.toLocaleString() + ' mi' : ''}`); } }
    if (S.mm !== 'hear') for (const [rc, h] of Object.entries(HEARD)) { if (now - h.t > 1800) { delete HEARD[rc]; continue; } const ll = g2ll(h.g); if (!ll) continue; m++;
      L.marker(ll, { icon: L.divIcon({ className: 'f8-tri', html: '▲', iconSize: [16, 16] }) }).addTo(ML).bindTooltip(`${rc} heard you ${fmtDb(h.snr)}${me ? ' · ' + distB(me, ll).mi.toLocaleString() + ' mi' : ''} · ${utc(h.t)}z`); }
    $('f8MapT').textContent = (S.mm !== 'me' ? n + ' heard' : '') + (S.mm === 'both' ? ' · ' : '') + (S.mm !== 'hear' ? m + ' heard you' + (pskT ? '' : ' (after you transmit)') : '');
  }
  $('f8MapW').addEventListener('toggle', () => { if ($('f8MapW').open) { setTimeout(() => { mapInit(); if (MAP) { MAP.invalidateSize(); mapDraw(); } }, 60); if (S.mm !== 'hear' && S.mode !== 'WSPR') psk(); if (S.mode === 'WSPR' && DG()) DG().mapOpen(); } });
  document.querySelectorAll('[data-mm]').forEach(b => b.onclick = e => { e.preventDefault(); S.mm = b.dataset.mm; saveS(); document.querySelectorAll('[data-mm]').forEach(x => x.classList.toggle('on', x === b)); if (!$('f8MapW').open) $('f8MapW').open = true; if (S.mm !== 'hear') psk(); mapDraw(); });
  document.querySelectorAll('[data-mm]').forEach(x => x.classList.toggle('on', x.dataset.mm === S.mm));
  /* Oct 18 (Brandon: 'showed no one heard me'): say how long since we listened / last report, and link PSK Reporter's own map to double-check */
  let pskSince = 0;
  function pskSay() { const n = Object.keys(HEARD).length, me = myCall(); if (!pskSince) pskSince = nowS();
    const mins = Math.round((nowS() - pskSince) / 60), last = pskT ? Math.round((nowS() - pskT) / 60) : null;
    $('f8PskT').innerHTML = `· PSK Reporter live: ${n ? n + ' station' + (n > 1 ? 's' : '') + ' heard you' + (last != null ? ', last ' + (last < 1 ? 'just now' : last + ' min ago') : '') : 'listening ' + mins + ' min, nobody yet (reports can take 5-10 min to arrive)'}` +
      (me ? ` · <a href="https://pskreporter.info/pskmap.html?preset&callsign=${encodeURIComponent(me)}&timerange=3600&txrx=tx" target="_blank" rel="noopener">CHECK ON PSK REPORTER ›</a>` : ''); }
  setInterval(() => { if (mqC && mqC.connected && !root.hidden) pskSay(); }, 60000);
  /* PSK Reporter's live feed (MQTT over a secure websocket, mqtt.pskreporter.info:1886): every station that hears my call */
  function psk() {
    const me = myCall(); if (!me || mqFor === me) return;
    const go = () => { try { if (mqC) mqC.end(true); mqFor = me;
      mqC = window.mqtt.connect('wss://mqtt.pskreporter.info:1886', { reconnectPeriod: 30000, connectTimeout: 15000 });
      mqC.on('connect', () => { mqC.subscribe(`pskr/filter/v2/+/+/${me}/#`); pskSay(); });
      mqC.on('error', () => { $('f8PskT').textContent = '· PSK Reporter live feed not answering'; });
      mqC.on('offline', () => { $('f8PskT').textContent = '· PSK Reporter live feed offline (no signal?)'; });
      mqC.on('message', (t, b) => { try { const j = JSON.parse(new TextDecoder().decode(b)); if (!j.rc || !j.rl) return; pskT = nowS(); HEARD[j.rc] = { g: j.rl, snr: +j.rp || 0, t: +j.t || nowS(), f: j.f, md: j.md }; pskSay(); if ($('f8MapW').open) mapDraw(); } catch (e) {} });
    } catch (e) { mqFor = ''; } };
    if (window.mqtt) go(); else { const sc = document.createElement('script'); sc.src = 'https://unpkg.com/mqtt@5.10.1/dist/mqtt.min.js'; sc.onload = go; sc.onerror = () => { mqFor = ''; $('f8PskT').textContent = '· PSK Reporter could not load (no signal?)'; }; document.head.appendChild(sc); }
  }

  /* ---------------- messages + sequencer ---------------- */
  const QS = { dx: '', grid: '', rs: '-10', rr: '', state: 'idle', next: 6, logged: false, tries: 0, since: 0, ref: '', cq: false };
  function myCall() { const L = LG(); return L ? String(L.me().station || L.me().call || '').toUpperCase() : ''; }
  /* Oct 17 (Brandon: 'it does not enter my grid square… like it should, auto location'): station grid, else the park's pin, else this device's GPS */
  let GPSG = get('kpcFt8Gps', null), gpsAsk = 0;
  const ll2g = (la, lo) => { const x = lo + 180, y = la + 90; return String.fromCharCode(65 + Math.floor(x / 20), 65 + Math.floor(y / 10)) + Math.floor((x % 20) / 2) + Math.floor(y % 10); };
  function myGrid() { const L = LG(), me = L ? L.me() : {}; const g = String(me.grid || me.pgrid || '').slice(0, 4).toUpperCase(); if (/^[A-R]{2}\d\d$/.test(g)) return g;
    if (GPSG && GPSG.g && Date.now() - GPSG.t < 6 * 3600e3) return GPSG.g; gpsGrid(); return GPSG && GPSG.g || ''; }
  function gpsGrid() { if (!navigator.geolocation || Date.now() - gpsAsk < 120e3) return; gpsAsk = Date.now();
    navigator.geolocation.getCurrentPosition(p => { const g = ll2g(p.coords.latitude, p.coords.longitude), was = GPSG && GPSG.g; GPSG = { g, t: Date.now() }; put('kpcFt8Gps', GPSG);
      if (was !== g) { try { gen(); } catch (e) {} note('📍 Your grid ' + g + ' (from this device\'s GPS) is in your messages now.', 4000); } }, () => {}, { enableHighAccuracy: false, timeout: 15000, maximumAge: 600000 }); }
  function cqWord() { const L = LG(), me = L ? L.me() : {}; if (S.cqw === 'POTA' && me.hunt) return ''; return S.cqw; }
  function gen() {
    const me = myCall() || 'K4TEST', g = myGrid(), dx = (QS.dx || 'DXCALL'), r = QS.rs || '-10', rr = QS.rr ? QS.rr : r;
    const M = [`${dx} ${me}${g ? ' ' + g : ''}`, `${dx} ${me} ${r}`, `${dx} ${me} R${r}`, `${dx} ${me} RR73`, `${dx} ${me} 73`, `CQ ${cqWord() ? cqWord() + ' ' : ''}${me}${g ? ' ' + g : ''}`];
    $('f8Txm').innerHTML = M.map((m, i) => `<div class="f8-tm${QS.next === i + 1 ? ' on' : ''}"><button type="button" class="nx" data-nx="${i + 1}" title="Send this one next">Tx${i + 1}</button><input data-tm="${i + 1}" value="${esc(m)}" spellcheck="false" autocapitalize="characters"><button type="button" class="nw" data-now="${i + 1}" title="Send this one now">NOW</button></div>`).join('');
    void rr;
  }
  const msgOf = n => { const i = document.querySelector(`[data-tm="${n}"]`); return i ? i.value.toUpperCase().trim() : ''; };
  function nextTx(n) { QS.next = n; document.querySelectorAll('.f8-tm').forEach((d, i) => d.classList.toggle('on', i + 1 === n)); }
  $('f8Txm').addEventListener('click', e => { const a = e.target.closest('[data-nx]'), b = e.target.closest('[data-now]');
    if (a) nextTx(+a.dataset.nx); if (b) { nextTx(+b.dataset.now); txOn(true); NOWTX = true; } });
  let TXON = false, TXING = false, NOWTX = false, TUNE = null;
  function txOn(on) { TXON = !!on; if (on && !RUN) startAudio(); if (on) QS.since = QS.since || nowS(); chk(); stat(); }
  function chk() { $('f8En').classList.toggle('on', TXON); $('f8Cq').classList.toggle('on', TXON && QS.next === 6); }
  function stat() { const e = $('f8St'); e.textContent = TXING ? 'TX ' + (TUNE ? 'TUNE' : '') : RUN ? (TXON ? 'RX · TX ON' : 'RX') : 'OFF'; e.className = 'f8-st ' + (TXING ? 'tx' : RUN ? 'rx' : ''); }
  $('f8En').onclick = () => { if (!RUN) { startAudio().then(ok => ok && txOn(!TXON)); return; } txOn(!TXON); };
  $('f8Halt').onclick = () => halt('Stopped.');
  $('f8Cq').onclick = () => { if (!myCall()) { note('Put YOUR call in ⚙ STATION first.'); const L = LG(); if (L) { back(); L.station(); } return; }
    QS.dx = ''; QS.grid = ''; QS.state = 'cq'; QS.logged = false; QS.cq = true; QS.ref = ''; QS.since = nowS(); $('f8Dx').value = ''; $('f8DxG').value = ''; gen(); nextTx(6); txOn(true); };
  $('f8Gen').onclick = () => { QS.dx = clean($('f8Dx').value); QS.grid = $('f8DxG').value.toUpperCase(); QS.rs = $('f8Rpt').value.trim() || QS.rs; gen(); };
  $('f8Dx').oninput = e => { e.target.value = e.target.value.toUpperCase().replace(/\s/g, ''); };
  $('f8Dx').onchange = () => { QS.dx = clean($('f8Dx').value); QS.logged = false; QS.state = 'call'; gen(); };
  $('f8DxG').oninput = e => { e.target.value = e.target.value.toUpperCase(); };
  $('f8Rpt').onchange = () => { QS.rs = $('f8Rpt').value.trim(); gen(); };
  function halt(why) { TXON = false; NOWTX = false; if (TXING) stopTx(); chk(); stat(); if (why) note(why, 2500); }
  $('f8Tune').onclick = async () => { if (TXING && TUNE) { stopTx(); return; }
    /* Android: TUNE without START = the mic is never opened (same as playing a video). Test for low power (Brandon Oct 18) */
    if (!RUN && mediaOut()) { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); try { await AC.resume(); } catch (e) {} startTone(); note('TUNE with the mic closed (not listening).', 3000); return; }
    if (!RUN && !(await startAudio())) return; startTone(); };

  /* the sequencer: read what came in this slot and pick the next message (WSJT-X auto sequence) */
  function seq(sl, D) {
    const me = myCall(); if (!me || !S.auto) return;
    const L = LINES.filter(x => x.sl === sl && x.me);
    let mine = L.find(x => QS.dx && x.fr === QS.dx);
    if (!mine && (QS.state === 'cq' || (QS.next === 6 && TXON)) && L.length) {
      /* someone answered my CQ: Call 1st = the first one, else the strongest */
      const c = L.slice().sort((a, b) => S.first ? 0 : b.db - a.db)[0];
      if (c && c.fr && !/\.\.\./.test(c.fr)) { QS.dx = c.fr; QS.grid = c.grid || ''; QS.rs = fmtDb(c.db); QS.rr = ''; QS.logged = false; QS.tries = 0; QS.since = nowS(); QS.ref = ''; S.even = c.par === 1; $('f8Dx').value = QS.dx; $('f8DxG').value = QS.grid; $('f8Rpt').value = QS.rs; mine = c; }
    }
    if (!mine) { /* watchdog: 6 minutes of calling with no answer */ const wd = (+S.wd || 2) * 60; if (TXON && QS.since && nowS() - QS.since > wd) { halt(`⏱ No answer for ${S.wd || 2} minute${(+S.wd || 2) > 1 ? 's' : ''}: TX turned off. Change this in ⚙ SETTINGS.`); QS.since = 0; } return; }
    const tk = mine.text.split(/\s+/), last = tk[tk.length - 1].toUpperCase();
    QS.since = nowS(); if (!QS.rs) QS.rs = fmtDb(mine.db);
    S.even = mine.par === 1;
    if (isGrid(last) || tk.length === 2) { if (isGrid(last)) QS.grid = last; gen(); nextTx(2); QS.state = 'sentrpt'; }
    else if (isRpt(last)) { QS.rr = last; gen(); nextTx(3); QS.state = 'sentrrpt'; }
    else if (isRRpt(last)) { QS.rr = last.slice(1); gen(); nextTx(4); QS.state = 'rr73'; /* logged when RR73 goes out */ }
    else if (last === 'RR73' || last === 'RRR') { if (!QS.logged) logIt(); nextTx(5); QS.state = 'send73'; }
    else if (last === '73') { if (!QS.logged && QS.rr) logIt(); afterQso(); }
    $('f8DxG').value = QS.grid; $('f8Rpt').value = QS.rs; if (!TXON && QS.state !== 'done') txOn(true);
    chk(); drawRx();
  }
  function afterQso() {
    QS.state = 'done';
    if (S.keepCq && QS.cq) { QS.dx = ''; QS.grid = ''; QS.rr = ''; QS.logged = false; QS.state = 'cq'; QS.since = nowS(); $('f8Dx').value = ''; $('f8DxG').value = ''; gen(); nextTx(6); }
    else { TXON = false; chk(); stat(); }
  }
  let LAST = { k: '', t: 0 };
  function logIt() {
    const L = LG(); if (!L || !QS.dx) return; QS.logged = true;
    /* the same contact again (they missed my RR73 and sent R-report again): don't log it twice */
    const k = QS.dx + '|' + S.band + '|' + S.mode; if (LAST.k === k && nowS() - LAST.t < 900) return; LAST = { k, t: nowS() };
    const r = L.add({ call: QS.dx, khz: dialK(), mode: S.mode, rs: QS.rs, rr: QS.rr, g: QS.grid, ref: QS.ref });
    if (r && r.ok) note(`✅ ${QS.dx} logged · ${S.band} ${S.mode} · sent ${QS.rs} rcvd ${QS.rr || '?'}${r.n ? ' · ' + r.n + (L.me().hunt ? ' today' : ' this activation') : ''}`, 3000, 'log');
    else note('⚠️ Not logged: ' + ((r && r.msg) || 'the logger did not answer'), 5000);
  }

  /* ---------------- transmit ---------------- */
  let TXSRC = null, txStopT = null, lastTxSlot = -1;
  async function ptt(on) { if (S.ptt === 'vox' || !window.KPCCat) return; try { await KPCCat.ptt(on, S.ptt); } catch (e) {} }
  function txTick(t, sl, into) {
    if (!RUN || TXING || !TXON || !ENG) return;
    const par = sl % 2, wantPar = S.even ? 0 : 1; if (par !== wantPar) return;
    if (lastTxSlot === sl) return;
    const late = S.mode === 'FT4' ? 1.2 : 2.5; if (into > late && !NOWTX) return;
    if (into > (S.mode === 'FT4' ? 3 : 8)) return;
    if (!myCall()) { halt(); note('Put YOUR call in ⚙ STATION first: nothing was sent.', 5000); return; }
    lastTxSlot = sl; NOWTX = false;
    const n = QS.next || 6; let m = msgOf(n); if (!m) return;
    if (/DXCALL/.test(m) && clean($('f8Dx').value)) { QS.dx = clean($('f8Dx').value); gen(); m = msgOf(n); }
    if (/DXCALL/.test(m)) { note('Pick a station first (tap a line), or press 📣 CQ.'); halt(); return; }
    const tones = ENG.tones(m, S.mode === 'FT4'); if (!tones) { note('⚠️ That message can\'t be sent in ' + S.mode + ': ' + m, 5000); halt(); return; }
    sendTones(tones, sl, Math.max(0, 0.5 - into), m, n);
  }
  /* Oct 18 (Brandon: YouTube through the same cord = 50 W, our page = 1-10 W): on Android, send the sound the way a video plays it
     (a media player, like FT8CN's 'media' sound) instead of the live sound mixer. S.txOut = 'webaudio' goes back to the old way. */
  function mediaOut() { return ANDR && S.txOut !== 'webaudio'; }
  function wavBlob(x, rate) { const n = x.length, b = new ArrayBuffer(44 + n * 2), v = new DataView(b), w = (o, t) => { for (let i = 0; i < t.length; i++) v.setUint8(o + i, t.charCodeAt(i)); };
    w(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); w(8, 'WAVE'); w(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); w(36, 'data'); v.setUint32(40, n * 2, true);
    for (let i = 0; i < n; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, x[i])) * 32767, true); return new Blob([b], { type: 'audio/wav' }); }
  /* looks like an AudioBufferSourceNode: start(at, offset), stop(), onended */
  function mediaSrc(x, rate) { const url = URL.createObjectURL(wavBlob(x, rate)), el = new Audio(url), o = { onended: null, el };
    el.preload = 'auto'; el.volume = Math.min(1, S.lvl); el.onended = () => { URL.revokeObjectURL(url); if (o.onended) o.onended(); };
    o.start = (at, off) => { const d = Math.max(0, (at - AC.currentTime) * 1000 - 60); setTimeout(() => { if (o.dead) return; try { if (off) el.currentTime = off; } catch (e) {} el.play().catch(e => note('⚠️ The tablet would not play the sound: ' + (e.message || e), 6000)); }, d); };
    o.stop = () => { o.dead = true; try { el.pause(); } catch (e) {} URL.revokeObjectURL(url); }; return o; }
  async function sendTones(tones, sl, wait, m, n) {
    TXING = true; stat(); txSlots.add(S.mode + sl); psk();
    const rate = AC.sampleRate, au = KPCFT8.synth(tones, S.txHz, rate, S.mode === 'FT4');
    const into0 = nowS() - sl * slotLen(); /* started late = skip the part already gone, like WSJT-X */
    const skip = Math.max(0, Math.round((into0 - 0.5 + wait) * rate));
    let src;
    if (mediaOut()) { src = mediaSrc(au, rate); TXSRC = src; }
    else { const b = AC.createBuffer(1, au.length, rate); b.copyToChannel(au, 0);
      const g = AC.createGain(); g.gain.value = S.lvl; (window.__kpcTxG = (window.__kpcTxG || []).filter(x => x.context === g.context).slice(-6)).push(g); src = AC.createBufferSource(); src.buffer = b; src.connect(g); g.connect(AC.destination); TXSRC = src; }
    txMicOff(); await ptt(true);
    const at = AC.currentTime + Math.max(0.05, wait);
    src.start(at, skip / rate);
    MYQ.push({ t: sl * slotLen(), tx: 1, hz: S.txHz, text: m }); if (MYQ.length > 40) MYQ.shift(); drawRx();
    const dur = au.length / rate - skip / rate;
    src.onended = () => { if (TXSRC === src) stopTx(); };
    clearTimeout(txStopT); txStopT = setTimeout(() => { if (TXSRC === src) stopTx(); }, (dur + wait + 0.4) * 1000);
    /* RR73 / 73 sent: WSJT-X logs here when I'm the one who called CQ */
    if (n === 4) { if (!QS.logged) logIt(); setTimeout(afterQso, 300); }
    if (n === 5) { if (!QS.logged && QS.rr) logIt(); setTimeout(afterQso, 300); }
    if (n === 1 || n === 6) QS.tries++;
  }
  function stopTx() { try { TXSRC && TXSRC.stop(); } catch (e) {} TXSRC = null; TUNE = null; TXING = false; clearTimeout(txStopT); setTimeout(async () => { await ptt(false); txMicOn(); }, 80); stat(); }
  async function startTone() {
    if (!AC) return; TXING = true; let o;
    if (mediaOut()) { const r = AC.sampleRate, x = new Float32Array(r * 10); for (let i = 0; i < x.length; i++) x[i] = Math.sin(2 * Math.PI * S.txHz * i / r) * Math.min(1, i / 240, (x.length - i) / 240); o = mediaSrc(x, r); }
    else { o = AC.createOscillator(); const g = AC.createGain(); o.frequency.value = S.txHz; g.gain.value = S.lvl; (window.__kpcTxG = (window.__kpcTxG || []).filter(x => x.context === g.context).slice(-6)).push(g); o.connect(g); g.connect(AC.destination); }
    txMicOff(); await ptt(true); if (o.el) o.start(AC.currentTime); else o.start(); TUNE = o; TXSRC = o; stat(); clearTimeout(txStopT); txStopT = setTimeout(() => { if (TXSRC === o) stopTx(); }, 10000); note('TUNE: a steady tone for 10 s. Tap TUNE again to stop.', 2500);
  }

  /* ---------------- boxes, settings ---------------- */
  function hzBoxes() { $('f8TxHz').value = S.txHz; $('f8RxHzIn').value = S.rxHz; }
  $('f8TxHz').onchange = () => { S.txHz = Math.max(200, Math.min(3000, +$('f8TxHz').value || 1500)); saveS(); hzBoxes(); drawScale(); };
  $('f8RxHzIn').onchange = () => { S.rxHz = Math.max(200, Math.min(3000, +$('f8RxHzIn').value || 1500)); if (!S.hold) S.txHz = S.rxHz; saveS(); hzBoxes(); drawScale(); drawRx(); };
  const CK = { f8Auto: 'auto', f8First: 'first', f8Even: 'even', f8Hold: 'hold', f8Keep: 'keepCq', f8Deep: 'deep' };
  Object.keys(CK).forEach(id => { $(id).checked = !!S[CK[id]]; $(id).onchange = () => { S[CK[id]] = $(id).checked; saveS(); }; });
  /* TX level in dB, 0.5 dB steps, applied LIVE to whatever is playing (TUNE, FT8, CW tone, RTTY/PSK/SSTV/WSPR) so the ALC can be set while tuning */
  const lvlDb = () => Math.round(20 * Math.log10(Math.max(0.01, S.lvl)) * 2) / 2;
  function setLvl(db) { db = Math.max(-40, Math.min(0, Math.round(db * 2) / 2)); S.lvl = Math.pow(10, db / 20); saveS(); $('f8Pwr').value = db; $('f8PwrT').textContent = (db > 0 ? '+' : '') + db.toFixed(1) + ' dB';
    (window.__kpcTxG || []).forEach(g => { try { g.gain.setTargetAtTime(S.lvl, g.context.currentTime, 0.02); } catch (e) {} }); if (TXSRC && TXSRC.el) TXSRC.el.volume = Math.min(1, S.lvl); }
  function setRxg(db) { db = Math.max(-30, Math.min(20, Math.round(db))); S.rxg = db; saveS(); $('f8Rxg').value = db; $('f8RxgT').textContent = (db > 0 ? '+' : '') + db + ' dB';
    if (RXG) try { RXG.gain.setTargetAtTime(Math.pow(10, db / 20), RXG.context.currentTime, 0.05); } catch (e) {} }
  setRxg(+S.rxg || 0); $('f8Rxg').oninput = () => setRxg(+$('f8Rxg').value); $('f8RxgD').onclick = () => setRxg((+S.rxg || 0) - 2); $('f8RxgU').onclick = () => setRxg((+S.rxg || 0) + 2);
  setLvl(lvlDb()); $('f8Pwr').oninput = () => setLvl(+$('f8Pwr').value); $('f8PwrD').onclick = () => setLvl(lvlDb() - 0.5); $('f8PwrU').onclick = () => setLvl(lvlDb() + 0.5);
  $('f8Ptt').value = S.ptt; $('f8Ptt').onchange = () => { S.ptt = $('f8Ptt').value; saveS(); if (S.ptt !== 'vox' && window.KPCCat && !KPCCat.connected()) $('f8CatT').textContent = 'Connect the radio for this PTT choice.'; };
  const pf = () => { $('f8PotaF').classList.toggle('on', !!S.potaOnly); }; pf(); $('f8PotaF').onclick = () => { S.potaOnly = !S.potaOnly; saveS(); pf(); drawBand(); };
  ['aPark', 'aState', 'aGrid'].forEach(k => { const el = $('f8' + k); el.checked = !!S[k]; el.onchange = () => { S[k] = el.checked; saveS(); }; });
  $('f8Watch').value = S.watch || ''; $('f8Watch').onchange = () => { S.watch = $('f8Watch').value.toUpperCase(); $('f8Watch').value = S.watch; saveS(); };
  $('f8Wd').value = String(S.wd || 2); $('f8Wd').onchange = () => { S.wd = +$('f8Wd').value; saveS(); };
  /* no interface: the phone's own mic + speaker held next to the radio (Brandon Oct 17) */
  $('f8Mic').onclick = async () => { S.inDev = ''; S.outDev = ''; S.mic = true; S.ptt = 'vox'; S.lvl = Math.max(S.lvl, 0.8); saveS(); $('f8Ptt').value = 'vox'; setLvl(lvlDb()); $('f8MicT').hidden = false;
    if (RUN) { stopAudio(); } await startAudio(); devices(); note('🎤 Using this phone\'s mic and speaker. Radio VOX on, phone next to the radio.', 4000); };
  $('f8Cqw').value = S.cqw; $('f8Cqw').onchange = () => { S.cqw = $('f8Cqw').value; saveS(); gen(); };
  $('f8Cat').onclick = async () => { if (!window.KPCCat || !KPCCat.supported()) { $('f8CatT').textContent = 'Radio control needs Chrome or Edge on a computer, or Chrome on a newer Android phone with a USB-C cable. On iPhone use VOX.'; return; }
    KPCCat.set({ on: true }); const ok = await KPCCat.connect(true); $('f8CatT').textContent = ok ? '✓ Radio connected. Pick the radio type on the Lounge CAT & QRZ tab if it doesn\'t follow.' : 'Not connected.'; if (ok) radioTune(); };
  if (window.KPCCat) { KPCCat.onStatus((t) => { if (!root.hidden) $('f8CatT').textContent = t; }); if (!KPCCat.supported()) $('f8Cat').disabled = true; }
  hzBoxes(); gen(); nextTx(6); cwInit(); modeView(); drawScale();

  /* little note that fades away (Brandon: 'nothing extreme, short message that goes away') */
  let nT = null;
  function note(t, ms, kind) { const n = $('f8Note'); n.textContent = t; n.className = 'f8-note' + (kind ? ' ' + kind : ''); n.hidden = false; n.classList.remove('out'); clearTimeout(nT);
    nT = setTimeout(() => { n.classList.add('out'); setTimeout(() => { n.hidden = true; }, 400); }, ms || 3000); }
  $('f8Note').onclick = () => { $('f8Note').hidden = true; };

  /* ---------------- open / close the tab ---------------- */
  const main = $('lg') || $('hl') || root.parentElement;
  /* the free Hunters Lounge has no radio control (Brandon Oct 17: 'leave out qrz and cat control'): VOX and audio only there */
  if (main && main.id === 'hl') { $('f8Back').textContent = '← SPOTS'; }
  if (main && main.dataset.public === '1') { ['f8Ptt', 'cwVia'].forEach(id => { const el = $(id); if (el) [...el.options].forEach(o => { if (!/vox|audio/.test(o.value)) o.remove(); }); }); const cb = $('f8Cat'); if (cb) cb.parentElement.hidden = true; if (S.ptt !== 'vox') S.ptt = 'vox'; if (S.cwVia !== 'audio') S.cwVia = 'audio'; }
  /* Oct 17 (Brandon: the logger's hero text showed over the FT8 window): the panel starts right under the site header wherever the page is scrolled */
  function topFix() { const h = document.querySelector('header.site-nav'), b = h && !(main && getComputedStyle(main).position === 'fixed') ? Math.max(0, Math.round(h.getBoundingClientRect().bottom)) : 0; root.style.top = b + 'px'; }
  addEventListener('resize', () => { if (!root.hidden) topFix(); });
  function open() { root.hidden = false; topFix(); setTimeout(topFix, 80); main.setAttribute('data-ft8', ''); document.documentElement.classList.add('f8-open'); put('kpcFt8Open:' + location.pathname, 1); setTimeout(() => { wfSize(); drawScale(); drawBand(); drawRx(); }, 30); if (!myGrid()) note(main && main.id === 'hl' ? 'Tip: put your grid square in MY LOG FILES so your messages carry it.' : 'Tip: put your grid square in ⚙ STATION so your messages carry it.', 4000); }
  function back() { root.hidden = true; main.removeAttribute('data-ft8'); document.documentElement.classList.remove('f8-open'); put('kpcFt8Open:' + location.pathname, 0); }
  function tabDot() { document.querySelectorAll('[data-ft8open]').forEach(b => b.classList.toggle('live', RUN)); }
  $('f8Back').onclick = back;
  document.querySelectorAll('[data-ft8open]').forEach(b => b.onclick = open);
  addEventListener('keydown', e => { if (root.hidden) return; if (e.key === 'Escape' && TXING) halt('Stopped.'); });
  window.KPCFT8UI = {
    open, back,
    /* for kpc-digi-ui.js (RTTY / PSK31 / SSTV / WSPR) */
    host: { S, saveS, note, ptt, startAudio, ac: () => AC, running: () => RUN, myCall, myGrid, LG, dialK, nowS, utc, esc, g2ll, distB, stateOf, spotRef, drawScale, root, main,
      setTx(on) { TXING = !!on; stat(); }, txing: () => TXING, peak: (a, b) => peakIn(a, b), vals: () => lastVals, hzRange: () => [F0, F1], chime: () => chime(), xToHz: x => xToHz(x),
      map(hear, me) { XH = hear || []; XM = me || []; mapDraw(); }, setMode(m) { setMode(m); }, refresh() { bandOpts(); showDial(); modeView(); }, mapOpen: () => $('f8MapW').open },
    /* from the logger's spot list: tab over, set the band + their audio spot, and get ready to call them */
    go(o) {
      if (/^(RTTY|PSK31)$/.test(o.mode) && DG()) { open(); setMode(o.mode); const k = +o.khz; let best = null; for (const [b, f] of Object.entries(DIAL[S.mode])) { const off = (k - f) * 1000; if (off > -500 && off < 4000 && (!best || Math.abs(off - 1500) < Math.abs(best[1] - 1500))) best = [b, off]; }
        if (best) { S.band = best[0]; $('f8Band').value = S.band; saveS(); showDial(); radioTune(); } DG().go(o, best ? best[1] : null); return; }
      open(); const m = o.mode === 'FT4' ? 'FT4' : 'FT8'; if (m !== S.mode) { S.mode = m; bandOpts(); }
      const k = +o.khz; let best = null; for (const [b, f] of Object.entries(DIAL[S.mode])) { const off = (k - f) * 1000; if (off > -500 && off < 4000 && (!best || Math.abs(off - 1500) < Math.abs(best[1] - 1500))) best = [b, off]; }
      if (best) { S.band = best[0]; $('f8Band').value = S.band; if (best[1] >= 200 && best[1] <= 3000) { S.rxHz = Math.round(best[1]); } }
      saveS(); showDial(); radioTune(); hzBoxes(); drawScale();
      QS.dx = o.call; QS.grid = ''; QS.rr = ''; QS.logged = false; QS.state = 'call'; QS.cq = false; QS.ref = o.ref || ''; QS.since = nowS(); $('f8Dx').value = o.call; $('f8DxG').value = ''; gen(); nextTx(1);
      note(`Listening for ${o.call}${o.ref ? ' at ' + o.ref : ''}. When they show up, tap their line to call them${RUN ? '' : ' (press START LISTENING first)'}.`, 6000);
      drawRx();
    }
  };
  if (get('kpcFt8Open:' + location.pathname, 0) && location.hash !== '#nofT8') { /* stay on the FT8 screen after a reload */ setTimeout(open, 50); }
})();
