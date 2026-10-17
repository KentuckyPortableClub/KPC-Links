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
    FT4: { '80m': 3575, '40m': 7047.5, '30m': 10140, '20m': 14080, '17m': 18104, '15m': 21140, '12m': 24919, '10m': 28180, '6m': 50318 }
  };
  const S = Object.assign({ mode: 'FT8', band: '20m', inDev: '', outDev: '', ptt: 'vox', txHz: 1500, rxHz: 1500, hold: true, auto: true, first: true, even: true, keepCq: false, cqw: 'POTA', lvl: 0.3, deep: false, wd: 2 }, get('kpcFt8', {}));
  const saveS = () => put('kpcFt8', S);
  const slotLen = () => S.mode === 'FT4' ? 7.5 : 15;
  const dialK = () => (DIAL[S.mode] || DIAL.FT8)[S.band] || DIAL.FT8['20m'];
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
    <div class="f8-modes" role="group" aria-label="Mode"><button type="button" data-f8m="FT8">FT8</button><button type="button" data-f8m="FT4">FT4</button></div>
    <select id="f8Band" aria-label="Band"></select>
    <b class="f8-dial" id="f8Dial">14.074 000</b>
    <span class="f8-clk"><b id="f8Utc">--:--:--</b><i class="f8-slot"><i id="f8SlotBar"></i></i></span>
    <span class="f8-st" id="f8St">OFF</span>
  </div>
  <div class="f8-startbox" id="f8StartBox"><button type="button" class="f8-go" id="f8Start">🎧 START LISTENING</button><span>Plug your radio's audio into this phone or computer (USB sound card / Digirig / the radio's USB), then press START. The browser asks to use the "microphone": pick the radio's audio.</span></div>
  <div class="f8-wfw"><canvas id="f8Wf" height="150"></canvas><canvas id="f8Scale" height="18"></canvas></div>
  <div class="f8-lists">
    <section><h3>BAND ACTIVITY <small id="f8Cnt"></small></h3><div class="f8-list" id="f8Band1"></div></section>
    <section><h3>RX FREQUENCY · MY QSO <small id="f8RxHz"></small></h3><div class="f8-list" id="f8Rx"></div></section>
  </div>
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
      <label>RADIO AUDIO OUT<select id="f8Out"><option value="">Default output</option></select><small id="f8OutT"></small></label>
      <label>TX LEVEL<input type="range" id="f8Pwr" min="0.02" max="1" step="0.01"><small>turn it down until the radio's ALC barely moves</small></label>
      <label>PTT (KEYING THE RADIO)<select id="f8Ptt"><option value="vox">VOX (radio or interface keys on the audio)</option><option value="cat">CAT command (radio connected by USB)</option><option value="rts">RTS line (Digirig and many cables)</option><option value="dtr">DTR line</option></select></label>
      <label>CQ<select id="f8Cqw"><option value="">CQ</option><option value="POTA">CQ POTA</option><option value="SOTA">CQ SOTA</option><option value="WWFF">CQ WWFF</option></select></label>
      <label>STOP CALLING AFTER (NO ANSWER)<select id="f8Wd"><option value="1">1 minute</option><option value="2">2 minutes</option><option value="3">3 minutes</option><option value="5">5 minutes</option><option value="10">10 minutes</option></select></label>
      <label class="ck"><input type="checkbox" id="f8Deep"> Deeper decoding (finds weaker stations, uses more battery)</label>
      <div class="f8-catrow"><button type="button" class="f8-b" id="f8Mic">🎤 NO CABLE? USE THIS PHONE'S MIC + SPEAKER</button></div>
      <p class="f8-mic" id="f8MicT" hidden>Using the built-in mic and speaker: put the phone right next to the radio's speaker (radio volume about half), and the radio's mic close to the phone's speaker. Turn the radio's <b>VOX</b> on so it keys when the phone plays, and keep the room quiet. It works, but a cable (Digirig, the radio's USB) decodes far more stations.</p>
      <div class="f8-catrow"><button type="button" class="f8-b" id="f8Cat">📻 CONNECT MY RADIO (CAT)</button><span id="f8CatT"></span></div>
    </div>
    <p class="f8-help">How it works: it listens to the radio's audio and shows everyone it decodes each 15 seconds (FT4: 7.5 s). Tap a station to call them: the six messages fill in and TX turns on. With <b>Auto seq</b> on it answers by itself (grid → report → R-report → RR73 → 73) and the contact goes into your log as soon as it's complete. <b>📣 CQ</b> calls CQ (CQ POTA when you have a park number). Set the radio to USB (or DATA/USB-D), the dial on the FT8 frequency, and keep the TX audio low. Your computer's or phone's clock must be right within about a second (turn on "set time automatically"). Engine: ft8_lib by Karlis Goba (MIT license). Practice calls on this page: K4TEST.</p>
  </details>
  <div class="f8-note" id="f8Note" hidden></div>`;

  /* band + mode controls */
  function bandOpts() { $('f8Band').innerHTML = Object.keys(DIAL[S.mode]).map(b => `<option${b === S.band ? ' selected' : ''}>${b}</option>`).join(''); if (!DIAL[S.mode][S.band]) { S.band = '20m'; $('f8Band').value = '20m'; } }
  function showDial() { const k = dialK(); $('f8Dial').textContent = (k / 1000).toFixed(6).replace(/(\.\d{3})(\d{3})$/, '$1 $2'); document.querySelectorAll('[data-f8m]').forEach(b => b.classList.toggle('on', b.dataset.f8m === S.mode)); }
  function radioTune() { if (window.KPCCat && KPCCat.get().on) KPCCat.tune(dialK(), 'DATA'); }
  function setMode(m) { if (m === S.mode) return; S.mode = m; saveS(); bandOpts(); showDial(); radioTune(); resetEng(); gen(); slotSep(true); }
  bandOpts(); showDial();
  document.querySelectorAll('[data-f8m]').forEach(b => b.onclick = () => setMode(b.dataset.f8m));
  $('f8Band').onchange = () => { S.band = $('f8Band').value; saveS(); showDial(); radioTune(); slotSep(true); };

  /* ---------------- decoder engine ---------------- */
  let ENG = null, engP = null;
  const engine = () => engP || (engP = (window.KPCFT8 ? KPCFT8.load('kpc-ft8.wasm?v=20261017a') : Promise.reject(new Error('kpc-ft8.js missing'))).then(e => (ENG = e)));
  function resetEng() { /* the engine is started fresh for every slot */ }

  /* ---------------- audio ---------------- */
  let AC = null, SRC = null, NODE = null, AN = null, STREAM = null, RUN = false;
  const R12 = 12000, RING = R12 * 40; const ring = new Float32Array(RING); let n12 = 0, t0 = 0, peak = 0;
  /* resampler: windowed-sinc low-pass (5 kHz) + fractional step to 12 kHz */
  let rs = null;
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
      if (r.cnt >= r.pos) { let a = 0, j = r.hp; for (let k = 0; k < T; k++) { a += h[k] * r.hist[j]; j = (j + 1) % T; } ring[n12 % RING] = a; n12++; r.pos += r.ratio; }
    }
    if (r.cnt > 1e9) { r.cnt -= 1e8; r.pos -= 1e8; }
    peak = Math.max(peak * 0.9, pk);
    /* time of each 12 kHz sample: anchored to the clock, nudged slowly so it never jumps */
    const est = nowS() - n12 / R12 - 0.03; if (!t0 || Math.abs(est - t0) > 1) t0 = est; else t0 += (est - t0) * 0.02;
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
    AN = AC.createAnalyser(); AN.fftSize = AC.sampleRate > 30000 ? 8192 : 4096; AN.smoothingTimeConstant = 0; SRC.connect(AN);
    try {
      await AC.audioWorklet.addModule(URL.createObjectURL(new Blob([WK], { type: 'text/javascript' })));
      NODE = new AudioWorkletNode(AC, 'kpc-ft8-in'); NODE.port.onmessage = e => pushIn(e.data);
      const mute = AC.createGain(); mute.gain.value = 0; SRC.connect(NODE); NODE.connect(mute); mute.connect(AC.destination);
    } catch (e) {
      NODE = AC.createScriptProcessor(4096, 1, 1); NODE.onaudioprocess = ev => pushIn(ev.inputBuffer.getChannelData(0).slice(0));
      const mute = AC.createGain(); mute.gain.value = 0; SRC.connect(NODE); NODE.connect(mute); mute.connect(AC.destination);
    }
    RUN = true; $('f8StartBox').hidden = true; root.classList.add('run'); devices(); stat(); slotSep(true); wfLoop(); tabDot();
    return true;
  }
  function stopAudio() {
    RUN = false; try { STREAM && STREAM.getTracks().forEach(t => t.stop()); } catch (e) {} try { NODE && NODE.disconnect(); SRC && SRC.disconnect(); } catch (e) {}
    STREAM = SRC = NODE = null; $('f8StartBox').hidden = false; root.classList.remove('run'); stat(); tabDot();
  }
  async function devices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
    const d = await navigator.mediaDevices.enumerateDevices();
    const opt = (k, sel) => d.filter(x => x.kind === k).map((x, i) => `<option value="${esc(x.deviceId)}"${x.deviceId === sel ? ' selected' : ''}>${esc(x.label || (k === 'audioinput' ? 'Input ' : 'Output ') + (i + 1))}</option>`).join('');
    $('f8In').innerHTML = '<option value="">Default input</option>' + opt('audioinput', S.inDev);
    const outs = opt('audiooutput', S.outDev);
    $('f8Out').innerHTML = '<option value="">Default output</option>' + outs;
    const can = AC ? !!AC.setSinkId : !!(window.AudioContext && AudioContext.prototype.setSinkId);
    $('f8Out').disabled = !can; $('f8OutT').textContent = can ? '' : 'This browser plays through the phone / computer\'s default output: pick the radio there (iPhone: plug in the interface).';
  }
  $('f8In').onchange = async () => { S.inDev = $('f8In').value; saveS(); if (RUN) { stopAudio(); await startAudio(); } };
  $('f8Out').onchange = async () => { S.outDev = $('f8Out').value; saveS(); if (AC && AC.setSinkId) { try { await AC.setSinkId(S.outDev); } catch (e) { note('Could not use that output.'); } } };
  $('f8Start').onclick = startAudio;

  /* ---------------- waterfall ---------------- */
  const wf = $('f8Wf'), sc = $('f8Scale'); let wfRow = null, lastSlotLine = 0;
  const F0 = 100, F1 = 3100;
  function wfSize() { const w = Math.max(300, Math.round(wf.clientWidth || 600)); if (wf.width !== w) { wf.width = w; sc.width = w; drawScale(); } }
  const hzToX = hz => (hz - F0) / (F1 - F0) * wf.width;
  const xToHz = x => Math.round(F0 + x / wf.width * (F1 - F0));
  function drawScale() {
    const g = sc.getContext('2d'); g.clearRect(0, 0, sc.width, sc.height); g.fillStyle = '#0b0805'; g.fillRect(0, 0, sc.width, sc.height);
    g.fillStyle = '#c9b48a'; g.font = '10px monospace'; g.strokeStyle = '#6b5a3a';
    for (let hz = 500; hz < F1; hz += 500) { const x = hzToX(hz); g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 5); g.stroke(); g.fillText(String(hz), x - 12, 15); }
    const mark = (hz, c, w) => { const x = hzToX(hz), bw = (S.mode === 'FT4' ? 83 : 50) / (F1 - F0) * sc.width; g.fillStyle = c; g.fillRect(x, 0, Math.max(2, bw), w); };
    mark(S.rxHz, '#45e08f', 4); mark(S.txHz, '#ff5c5c', 3);
  }
  const COL = v => { v = Math.max(0, Math.min(1, v)); const r = v < .5 ? 0 : Math.round((v - .5) * 2 * 255), gg = v < .5 ? Math.round(v * 2 * 200) : 200 + Math.round((v - .5) * 110), b = v < .5 ? 90 + Math.round(v * 2 * 120) : Math.round(210 * (1 - (v - .5) * 2)); return [r, Math.min(255, gg), b]; };
  let wfT = 0;
  function wfLoop() {
    if (!RUN) return; requestAnimationFrame(wfLoop);
    const t = performance.now(); if (t - wfT < (S.mode === 'FT4' ? 60 : 120) || document.hidden || root.hidden) return; wfT = t;
    wfSize(); const g = wf.getContext('2d'), W = wf.width, H = wf.height;
    const n = AN.frequencyBinCount, d = new Float32Array(n); AN.getFloatFrequencyData(d);
    const binHz = AC.sampleRate / AN.fftSize, row = g.createImageData(W, 1), vals = new Float32Array(W);
    for (let x = 0; x < W; x++) { const hz = xToHz(x), b = Math.min(n - 1, Math.round(hz / binHz)); vals[x] = d[b]; }
    const sorted = Array.from(vals).sort((a, b) => a - b), med = sorted[Math.floor(W * 0.4)] || -100;
    for (let x = 0; x < W; x++) { const [r, gg, b] = COL((vals[x] - med + 2) / 26); row.data[x * 4] = r; row.data[x * 4 + 1] = gg; row.data[x * 4 + 2] = b; row.data[x * 4 + 3] = 255; }
    g.drawImage(wf, 0, 0, W, H - 1, 0, 1, W, H - 1); g.putImageData(row, 0, 0);
    const sl = Math.floor(nowS() / slotLen()); if (sl !== lastSlotLine) { lastSlotLine = sl; g.fillStyle = 'rgba(240,201,107,.75)'; g.fillRect(0, 0, W, 1); g.font = '10px monospace'; g.fillText(utc(sl * slotLen(), true), 4, 11); }
    /* level meter (dB above full-scale silence) */
    const db = peak > 0 ? 20 * Math.log10(peak) + 90 : 0; $('f8Lvl').style.width = Math.max(0, Math.min(100, db)) + '%'; $('f8Lvl').className = db < 20 || db > 80 ? 'bad' : '';
    $('f8LvlT').textContent = Math.round(db) + ' dB ' + (db < 20 ? '(too low: turn the radio\'s audio up)' : db > 80 ? '(too high: turn it down)' : '(good)');
  }
  wf.addEventListener('click', e => { const r = wf.getBoundingClientRect(), hz = xToHz((e.clientX - r.left) * wf.width / r.width); if (e.shiftKey) S.txHz = hz; else { S.rxHz = hz; if (!S.hold) S.txHz = hz; } saveS(); hzBoxes(); drawScale(); drawRx(); });
  wf.addEventListener('contextmenu', e => { e.preventDefault(); const r = wf.getBoundingClientRect(); S.txHz = xToHz((e.clientX - r.left) * wf.width / r.width); saveS(); hzBoxes(); drawScale(); });
  addEventListener('resize', () => { if (!root.hidden) wfSize(); });

  /* ---------------- decodes ---------------- */
  let LINES = [], lastDecSlot = -1, txSlots = new Set(), dtAvg = [];
  const MAXL = 400;
  function slotSep(force) { const sl = Math.floor(nowS() / slotLen()); if (force || !LINES.length || LINES[LINES.length - 1].sep !== sl) { /* separators come with each decode */ } }
  function tick() {
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
    $('f8Cnt').textContent = D.length + ' decoded';
    drawBand(); drawRx(); seq(sl, D);
  }
  function clockHint() { if (dtAvg.length < 3) return; const m = dtAvg.slice().sort((a, b) => a - b)[Math.floor(dtAvg.length / 2)]; if (Math.abs(m) > 1) note(`⏱ Most stations show DT ${m > 0 ? '+' : ''}${m.toFixed(1)} s: your clock is about ${Math.abs(m).toFixed(1)} s ${m > 0 ? 'slow' : 'fast'}. Turn on "set time automatically" or FT8 contacts may fail.`, 8000, 'clk'); }
  const spotRef = call => { const L = LG(); if (!L) return null; const s = (L.spots() || []).find(x => x.activator === call && x.reference && /FT8|FT4/i.test(x.mode || '')); return s || null; };
  function lineHtml(x) {
    if (x.sep != null) return `<div class="f8-sep">${utc(x.t, true).replace(/(\d\d)(\d\d)(\d\d)/, '$1:$2:$3')} ── ${x.mode}</div>`;
    const L = LG(), wk = L && x.fr && L.worked(x.fr), sp = x.cq ? spotRef(x.fr) : null, cls = x.tx ? 'tx' : x.me ? 'me' : x.cq ? (x.cqw ? 'cqp' : 'cq') : '';
    return `<div class="f8-l ${cls}${wk ? ' wk' : ''}" data-l="${x.id || ''}" role="button" tabindex="0"><span class="tm">${x.tx ? utc(x.t, true) : utc(x.t, true)}</span><span class="db">${x.tx ? 'Tx' : fmtDb(x.db)}</span><span class="dt">${x.tx ? '' : (x.dt >= 0 ? ' ' : '') + x.dt.toFixed(1)}</span><span class="hz">${x.hz}</span><span class="tx">${x.tx ? '~' : '~'}</span><span class="m">${esc(x.text)}${sp ? ` <i class="ref">🌲 ${esc(sp.reference)}</i>` : ''}${wk ? ' <i class="wkd">✓</i>' : ''}</span></div>`;
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
    if (!x || x.tx || x.sep != null) return;
    const me = myCall(); const other = x.me ? x.fr : (x.cq ? x.fr : (x.fr && x.fr !== me ? x.fr : x.to));
    if (!other || other === '...' || /\.\.\./.test(other)) { note('That call is hidden (a long or odd call sign). Wait for them to send their full call.'); return; }
    const keepG = QS.dx === other ? QS.grid : ''; QS.dx = other; QS.grid = x.grid || keepG; QS.rs = fmtDb(x.db); QS.rr = ''; QS.state = 'call'; QS.logged = false; QS.tries = 0; QS.since = nowS(); QS.ref = (spotRef(other) || {}).reference || QS.ref || '';
    S.rxHz = x.hz; if (!S.hold) S.txHz = x.hz; S.even = x.par === 1; saveS();
    $('f8Dx').value = QS.dx; $('f8DxG').value = QS.grid; $('f8Rpt').value = QS.rs;
    gen();
    /* answering them: if they're already calling me, jump ahead like WSJT-X */
    let n = 1; if (x.me) { const tk = x.text.split(/\s+/), last = tk[tk.length - 1]; if (isRpt(last)) { QS.rr = last; n = 3; } else if (isRRpt(last)) { QS.rr = last.slice(1); n = 4; } else if (last === 'RR73' || last === 'RRR') n = 5; else n = 2; }
    nextTx(n); txOn(true); hzBoxes(); drawScale(); drawRx(); chk();
  }
  ['f8Band1', 'f8Rx'].forEach(i => $(i).addEventListener('click', e => { const r = e.target.closest('[data-l]'); if (r) pick(byId[r.dataset.l]); }));
  ['f8Band1', 'f8Rx'].forEach(i => $(i).addEventListener('keydown', e => { if (e.key === 'Enter') { const r = e.target.closest('[data-l]'); if (r) pick(byId[r.dataset.l]); } }));

  /* ---------------- messages + sequencer ---------------- */
  const QS = { dx: '', grid: '', rs: '-10', rr: '', state: 'idle', next: 6, logged: false, tries: 0, since: 0, ref: '', cq: false };
  function myCall() { const L = LG(); return L ? String(L.me().station || L.me().call || '').toUpperCase() : ''; }
  function myGrid() { const L = LG(); return L ? String(L.me().grid || '').slice(0, 4).toUpperCase() : ''; }
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
  $('f8Tune').onclick = async () => { if (TXING && TUNE) { stopTx(); return; } if (!RUN && !(await startAudio())) return; startTone(); };

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
    const n = QS.next || 6, m = msgOf(n); if (!m) return;
    if (/DXCALL/.test(m)) { note('Pick a station first (tap a line), or press 📣 CQ.'); halt(); return; }
    const tones = ENG.tones(m, S.mode === 'FT4'); if (!tones) { note('⚠️ That message can\'t be sent in ' + S.mode + ': ' + m, 5000); halt(); return; }
    sendTones(tones, sl, Math.max(0, 0.5 - into), m, n);
  }
  async function sendTones(tones, sl, wait, m, n) {
    TXING = true; stat(); txSlots.add(S.mode + sl);
    const rate = AC.sampleRate, au = KPCFT8.synth(tones, S.txHz, rate, S.mode === 'FT4');
    const into0 = nowS() - sl * slotLen(); /* started late = skip the part already gone, like WSJT-X */
    const skip = Math.max(0, Math.round((into0 - 0.5 + wait) * rate));
    const b = AC.createBuffer(1, au.length, rate); b.copyToChannel(au, 0);
    const g = AC.createGain(); g.gain.value = S.lvl; const src = AC.createBufferSource(); src.buffer = b; src.connect(g); g.connect(AC.destination); TXSRC = src;
    await ptt(true);
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
  function stopTx() { try { TXSRC && TXSRC.stop(); } catch (e) {} TXSRC = null; TUNE = null; TXING = false; clearTimeout(txStopT); setTimeout(() => ptt(false), 80); stat(); }
  async function startTone() {
    if (!AC) return; TXING = true; const o = AC.createOscillator(), g = AC.createGain(); o.frequency.value = S.txHz; g.gain.value = S.lvl; o.connect(g); g.connect(AC.destination);
    await ptt(true); o.start(); TUNE = o; TXSRC = o; stat(); clearTimeout(txStopT); txStopT = setTimeout(() => { if (TXSRC === o) stopTx(); }, 10000); note('TUNE: a steady tone for 10 s. Tap TUNE again to stop.', 2500);
  }

  /* ---------------- boxes, settings ---------------- */
  function hzBoxes() { $('f8TxHz').value = S.txHz; $('f8RxHzIn').value = S.rxHz; }
  $('f8TxHz').onchange = () => { S.txHz = Math.max(200, Math.min(3000, +$('f8TxHz').value || 1500)); saveS(); hzBoxes(); drawScale(); };
  $('f8RxHzIn').onchange = () => { S.rxHz = Math.max(200, Math.min(3000, +$('f8RxHzIn').value || 1500)); if (!S.hold) S.txHz = S.rxHz; saveS(); hzBoxes(); drawScale(); drawRx(); };
  const CK = { f8Auto: 'auto', f8First: 'first', f8Even: 'even', f8Hold: 'hold', f8Keep: 'keepCq', f8Deep: 'deep' };
  Object.keys(CK).forEach(id => { $(id).checked = !!S[CK[id]]; $(id).onchange = () => { S[CK[id]] = $(id).checked; saveS(); }; });
  $('f8Pwr').value = S.lvl; $('f8Pwr').oninput = () => { S.lvl = +$('f8Pwr').value; saveS(); };
  $('f8Ptt').value = S.ptt; $('f8Ptt').onchange = () => { S.ptt = $('f8Ptt').value; saveS(); if (S.ptt !== 'vox' && window.KPCCat && !KPCCat.connected()) $('f8CatT').textContent = 'Connect the radio for this PTT choice.'; };
  $('f8Wd').value = String(S.wd || 2); $('f8Wd').onchange = () => { S.wd = +$('f8Wd').value; saveS(); };
  /* no interface: the phone's own mic + speaker held next to the radio (Brandon Oct 17) */
  $('f8Mic').onclick = async () => { S.inDev = ''; S.outDev = ''; S.ptt = 'vox'; S.lvl = Math.max(S.lvl, 0.8); saveS(); $('f8Ptt').value = 'vox'; $('f8Pwr').value = S.lvl; $('f8MicT').hidden = false;
    if (RUN) { stopAudio(); } await startAudio(); devices(); note('🎤 Using this phone\'s mic and speaker. Radio VOX on, phone next to the radio.', 4000); };
  $('f8Cqw').value = S.cqw; $('f8Cqw').onchange = () => { S.cqw = $('f8Cqw').value; saveS(); gen(); };
  $('f8Cat').onclick = async () => { if (!window.KPCCat || !KPCCat.supported()) { $('f8CatT').textContent = 'Radio control needs Chrome or Edge on a computer. Use VOX on phones.'; return; }
    KPCCat.set({ on: true }); const ok = await KPCCat.connect(true); $('f8CatT').textContent = ok ? '✓ Radio connected. Pick the radio type on the Lounge CAT & QRZ tab if it doesn\'t follow.' : 'Not connected.'; if (ok) radioTune(); };
  if (window.KPCCat) { KPCCat.onStatus((t) => { if (!root.hidden) $('f8CatT').textContent = t; }); if (!KPCCat.supported()) $('f8Cat').disabled = true; }
  hzBoxes(); gen(); nextTx(6); drawScale();

  /* little note that fades away (Brandon: 'nothing extreme, short message that goes away') */
  let nT = null;
  function note(t, ms, kind) { const n = $('f8Note'); n.textContent = t; n.className = 'f8-note' + (kind ? ' ' + kind : ''); n.hidden = false; n.classList.remove('out'); clearTimeout(nT);
    nT = setTimeout(() => { n.classList.add('out'); setTimeout(() => { n.hidden = true; }, 400); }, ms || 3000); }
  $('f8Note').onclick = () => { $('f8Note').hidden = true; };

  /* ---------------- open / close the tab ---------------- */
  const main = $('lg');
  function open() { root.hidden = false; main.setAttribute('data-ft8', ''); document.documentElement.classList.add('f8-open'); put('kpcFt8Open', 1); setTimeout(() => { wfSize(); drawScale(); drawBand(); drawRx(); }, 30); if (!myGrid()) note('Tip: put your grid square in ⚙ STATION so your messages carry it.', 4000); }
  function back() { root.hidden = true; main.removeAttribute('data-ft8'); document.documentElement.classList.remove('f8-open'); put('kpcFt8Open', 0); }
  function tabDot() { document.querySelectorAll('[data-ft8open]').forEach(b => b.classList.toggle('live', RUN)); }
  $('f8Back').onclick = back;
  document.querySelectorAll('[data-ft8open]').forEach(b => b.onclick = open);
  addEventListener('keydown', e => { if (root.hidden) return; if (e.key === 'Escape' && TXING) halt('Stopped.'); });
  window.KPCFT8UI = {
    open, back,
    /* from the logger's spot list: tab over, set the band + their audio spot, and get ready to call them */
    go(o) {
      open(); const m = o.mode === 'FT4' ? 'FT4' : 'FT8'; if (m !== S.mode) { S.mode = m; bandOpts(); }
      const k = +o.khz; let best = null; for (const [b, f] of Object.entries(DIAL[S.mode])) { const off = (k - f) * 1000; if (off > -500 && off < 4000 && (!best || Math.abs(off - 1500) < Math.abs(best[1] - 1500))) best = [b, off]; }
      if (best) { S.band = best[0]; $('f8Band').value = S.band; if (best[1] >= 200 && best[1] <= 3000) { S.rxHz = Math.round(best[1]); } }
      saveS(); showDial(); radioTune(); hzBoxes(); drawScale();
      QS.dx = o.call; QS.grid = ''; QS.rr = ''; QS.logged = false; QS.state = 'call'; QS.cq = false; QS.ref = o.ref || ''; QS.since = nowS(); $('f8Dx').value = o.call; $('f8DxG').value = ''; gen(); nextTx(1);
      note(`Listening for ${o.call}${o.ref ? ' at ' + o.ref : ''}. When they show up, tap their line to call them${RUN ? '' : ' (press START LISTENING first)'}.`, 6000);
      drawRx();
    }
  };
  if (get('kpcFt8Open', 0) && location.hash !== '#nofT8') { /* stay on the FT8 screen after a reload */ setTimeout(open, 50); }
})();
