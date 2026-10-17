/* KPC digital modes screens: RTTY · PSK31 · SSTV · WSPR inside the DIGI / 📡 FT8 · CW tab (Brandon Oct 17 2026: 'go ahead with RTTY,
   PSK31, SSTV, WSPR'). Uses the FT8 tab's radio audio, waterfall, PTT and log (window.KPCFT8UI.host) and the sound math in kpc-digi.js.
   Load after kpc-logger-ft8.js. Settings live in the same localStorage kpcFt8 (S.dg). Nothing is sent anywhere except the audio to your
   radio and, for WSPR, one wspr.live look-up of who heard your call. */
(function () {
  const UI = window.KPCFT8UI, D = window.KPCDigi; if (!UI || !UI.host || !D) return;
  const H = UI.host, S = H.S, $ = id => document.getElementById(id), esc = H.esc;
  const R = 12000;
  S.dg = Object.assign({ rtty: { center: 1500, shift: 170, baud: 45.45, rev: false, afc: true }, psk: { hz: 1000, afc: true, sq: 35 }, sstv: { auto: true, tx: 'Martin 1', top: '{MY}', bot: '{REF} · 73', man: 'Martin 1' }, wspr: { tx: false, pct: 20, dbm: 23, hz: 1500 }, mac: null, rs: '599', srs: '595' }, S.dg || {});
  ['rtty', 'psk', 'sstv', 'wspr'].forEach(k => { S.dg[k] = Object.assign({}, { rtty: { center: 1500, shift: 170, baud: 45.45, rev: false, afc: true }, psk: { hz: 1000, afc: true, sq: 35 }, sstv: { auto: true, tx: 'Martin 1', top: '{MY}', bot: '{REF} · 73', man: 'Martin 1' }, wspr: { tx: false, pct: 20, dbm: 23, hz: 1500 } }[k], S.dg[k]); });
  const G = S.dg, save = () => H.saveS();
  let MODE = '';

  /* ---------------- screen ---------------- */
  const pw = [0, 3, 7, 10, 13, 17, 20, 23, 27, 30, 33, 37, 40, 43, 47, 50, 53, 57, 60];
  const wat = d => { const w = Math.pow(10, d / 10) / 1000; return w < 1 ? Math.round(w * 1000) + ' mW' : (w < 10 ? w.toFixed(1).replace(/\.0$/, '') : Math.round(w)) + ' W'; };
  const html = `
  <section class="dg" id="dgPane" aria-label="Digital modes">
    <div class="dg-kb">
      <div class="dg-set">
        <b class="dg-name" id="dgName">RTTY</b>
        <span class="dg-only-rtty">CENTER <b id="dgHzT">1500</b> Hz</span><span class="dg-only-psk">CARRIER <b id="dgPHzT">1000</b> Hz</span>
        <select id="dgShift" class="dg-only-rtty" aria-label="Shift"><option value="170">170 Hz shift</option><option value="200">200 Hz</option><option value="425">425 Hz</option><option value="850">850 Hz</option></select>
        <select id="dgBaud" class="dg-only-rtty" aria-label="Speed"><option value="45.45">45.45 baud</option><option value="50">50 baud</option><option value="75">75 baud</option></select>
        <label class="ck dg-only-rtty"><input type="checkbox" id="dgRev"> REV</label>
        <label class="ck"><input type="checkbox" id="dgAfc"> AFC</label>
        <label class="dg-sq dg-only-psk">SQUELCH<input type="range" id="dgSq" min="0" max="90" step="5"></label>
        <span class="dg-meter" title="Signal"><i id="dgQ"></i></span>
        <button type="button" class="f8-b" id="dgClr">CLEAR</button>
      </div>
      <div class="dg-br dg-only-psk" id="dgBr" aria-label="Every PSK31 signal on the waterfall"></div>
      <div class="dg-rx" id="dgRx" aria-live="polite"></div>
      <div class="cw-calls" id="dgCalls"></div>
    </div>
    <div class="dg-sstv">
      <div class="dg-set"><b class="dg-name">SSTV</b><span id="dgSst">Waiting for a picture…</span>
        <label class="ck"><input type="checkbox" id="dgAuto"> Start by itself (VIS code)</label>
        <select id="dgMan" aria-label="Mode for a manual start"></select><button type="button" class="f8-b" id="dgGo">▶ START NOW</button><button type="button" class="f8-b halt" id="dgStopRx">■ STOP</button></div>
      <div class="dg-pics"><canvas id="dgCv" width="320" height="256" aria-label="Picture being received"></canvas>
        <div class="dg-pact"><button type="button" class="f8-b" id="dgSave">💾 SAVE PICTURE</button><button type="button" class="f8-b" id="dgShare">📤 SHARE</button></div>
        <div class="dg-gal" id="dgGal"></div></div>
      <details class="dg-send" id="dgSend"><summary>📤 SEND A PICTURE</summary>
        <div class="dg-sg"><label>MODE<select id="dgTxMode"><option>Martin 1</option><option>Scottie 1</option><option>Robot 36</option><option>PD 120</option></select><small id="dgTxLen"></small></label>
          <label>PICTURE<span class="dg-pbtn"><button type="button" class="f8-b" id="dgPick">📷 PICK A PHOTO</button><button type="button" class="f8-b" id="dgCard">🪪 MY CARD</button></span><input type="file" id="dgFile" accept="image/*" hidden></label>
          <label>TEXT ON TOP<input id="dgTop" spellcheck="false" autocapitalize="characters"></label><label>TEXT ON THE BOTTOM<input id="dgBot" spellcheck="false" autocapitalize="characters"></label></div>
        <canvas id="dgTxCv" width="320" height="256" aria-label="Picture to send"></canvas>
        <div class="dg-txl"><button type="button" class="f8-b tx" id="dgTxGo">▶ SEND IT</button><button type="button" class="f8-b halt" id="dgTxStop">■ STOP</button><span id="dgTxT"></span></div>
        <p class="f8-help">Use {MY}, {REF} (your park), {GRID} in the text. Set the radio to the SSTV frequency (LSB on 80 and 40 m, USB above, FM for the ISS) and keep the power low: SSTV is a full-power steady signal for up to 2 minutes.</p>
      </details>
    </div>
    <div class="dg-log"><label>THEIR CALL<input id="dgCall" autocapitalize="characters" spellcheck="false"></label><label>SENT<input id="dgRs" maxlength="3"></label><label>RCVD<input id="dgRr" maxlength="3"></label><label>THEIR PARK<input id="dgRef" autocapitalize="characters" spellcheck="false" placeholder="optional"></label><button type="button" class="f8-b tx" id="dgLog">⬆ LOG IT</button></div>
    <div class="dg-kb2">
      <div class="cw-mac" id="dgMac"></div>
      <div class="cw-txl"><input id="dgTx" placeholder="Type here and press Enter to send it" autocapitalize="characters" spellcheck="false" autocomplete="off"><button type="button" class="f8-b tx" id="dgSendT">SEND</button><button type="button" class="f8-b halt" id="dgStop">STOP</button></div>
      <p class="f8-help">Tap a signal on the waterfall to tune to it (RTTY: tap between the two lines; PSK31: tap the signal, or tap a line in the list above to read it). Radio on USB or DATA. Sending uses the TX level and PTT from ⚙ AUDIO, PTT &amp; SETTINGS.</p>
    </div>
    <div class="dg-wspr">
      <div class="dg-set"><b class="dg-name">WSPR</b><span class="dg-clk">NEXT 2-MINUTE CYCLE <b id="dgWNext">--</b></span><span id="dgWSt">Listening…</span></div>
      <div class="dg-wtx"><label class="ck"><input type="checkbox" id="dgWTx"> Transmit my beacon</label>
        <select id="dgWPct" aria-label="How often"><option value="20">1 cycle in 5 (20%)</option><option value="33">1 in 3</option><option value="50">every other (50%)</option><option value="100">every cycle</option></select>
        <select id="dgWDbm" aria-label="My power">${pw.map(d => `<option value="${d}">${d} dBm (${wat(d)})</option>`).join('')}</select>
        <label class="hz">TX <input id="dgWHz" inputmode="numeric" maxlength="4"> Hz</label><button type="button" class="f8-b" id="dgWNow">TX NEXT CYCLE</button>
        <span class="dg-wmsg" id="dgWMsg"></span></div>
      <div class="f8-list dg-wl" id="dgWList"><div class="f8-empty">Decodes show here every 2 minutes (UTC even minutes). Dial on the WSPR frequency, radio on USB.</div></div>
      <div class="dg-wme"><button type="button" class="f8-b" id="dgWho">📍 WHO HEARD ME (LAST HOUR)</button><span id="dgWhoT"></span></div>
      <div class="f8-list dg-wl" id="dgWhoL" hidden></div>
      <p class="f8-help">WSPR is a beacon: you send your call, grid and power, and listening stations around the world report it to wsprnet / wspr.live. Nobody answers and nothing goes in your log. Use a plain call (no /P); grid from ⚙ STATION. Decoder: a port of WSJT-X's wsprd (K1JT, K9AN, GPL v3).</p>
    </div>
  </section>`;
  $('cwPane').insertAdjacentHTML('afterend', html);
  $('dgMan').innerHTML = Object.keys(D.SSTV).map(k => `<option${k === G.sstv.man ? ' selected' : ''}>${k}</option>`).join('');

  /* ---------------- shared bits ---------------- */
  const me = () => H.myCall() || '';
  const myRef = () => { const L = H.LG(), m = L ? L.me() : {}; return (m.pota && m.pota[0]) || ''; };
  const fill = t => String(t).replace(/\{MY\}/g, me() || 'K4TEST').replace(/\{THEIR\}/g, $('dgCall').value.trim().toUpperCase()).replace(/\{REF\}/g, myRef()).replace(/\{GRID\}/g, H.myGrid()).replace(/\{ST\}/g, H.stateOf(H.myGrid()) || '');
  const audioHz = () => MODE === 'RTTY' ? G.rtty.center : MODE === 'PSK31' ? G.psk.hz : MODE === 'WSPR' ? G.wspr.hz : 1500;
  let TXSRC = null, txT = null;
  async function play(buf, why, done) {
    const AC = H.ac() || (await H.startAudio(), H.ac()); if (!AC) { H.note('Press START LISTENING first.'); return false; }
    if (!me()) { H.note('Put YOUR call in ⚙ STATION first: nothing was sent.', 4000); return false; }
    stopTx(); const b = AC.createBuffer(1, buf.length, AC.sampleRate); b.copyToChannel(buf, 0);
    const g = AC.createGain(); g.gain.value = S.lvl; (window.__kpcTxG = (window.__kpcTxG || []).slice(-6)).push(g); const src = AC.createBufferSource(); src.buffer = b; src.connect(g); g.connect(AC.destination); TXSRC = src;
    H.setTx(true); await H.ptt(true); src.start(AC.currentTime + 0.12);
    src.onended = () => { if (TXSRC === src) { TXSRC = null; H.ptt(false); H.setTx(false); if (done) done(); } };
    return true;
  }
  function stopTx() { if (TXSRC) { const s = TXSRC; TXSRC = null; try { s.stop(); } catch (e) {} H.ptt(false); H.setTx(false); } }

  /* ---------------- RTTY / PSK31 keyboard modes ---------------- */
  let rtty = null, psk = null, txt = '', calls = [];
  const CALLRE = /\b((?:[A-Z]{1,2}|\d[A-Z])\d{1,2}[A-Z]{1,4})(?:\/[A-Z0-9]+)?\b/g;
  function rxChar(c) { txt = (txt + c).slice(-6000); if (/[\s]/.test(c)) callScan(); clearTimeout(rxChar.t); rxChar.t = setTimeout(drawRx, 80); }
  function drawRx() { const el = $('dgRx'), stick = el.scrollTop + el.clientHeight >= el.scrollHeight - 30; el.textContent = txt; if (stick) el.scrollTop = el.scrollHeight; }
  function callScan() { const tail = txt.slice(-160), my = me(); let m; CALLRE.lastIndex = 0; while ((m = CALLRE.exec(tail))) { const c = m[1]; if (c === my || /^(\d+[A-Z]+|[A-Z]+\d+)$/.test(c) && c.length < 4) continue; calls = [c].concat(calls.filter(x => x !== c)).slice(0, 8); }
    $('dgCalls').innerHTML = calls.map(c => { const sp = H.spotRef(c), L = H.LG(), wk = L && L.worked && L.worked(c); return `<button type="button" data-dgc="${esc(c)}" class="${sp ? 'park' : ''}${wk ? ' wk' : ''}">${esc(c)}${sp ? ' 🌲 ' + esc(sp.reference) : ''}${wk ? ' ✓' : ''}</button>`; }).join(''); }
  $('dgCalls').addEventListener('click', e => { const b = e.target.closest('[data-dgc]'); if (!b) return; $('dgCall').value = b.dataset.dgc; const sp = H.spotRef(b.dataset.dgc); if (sp) $('dgRef').value = sp.reference; });
  function mkRtty() { rtty = new D.RttyRx({ center: G.rtty.center, shift: G.rtty.shift, baud: G.rtty.baud, rev: G.rtty.rev }); let pend = ''; rtty.onChar = c => { /* squelch: noise passes only about half the stop bits, a real signal nearly all */ if (rtty.q > 0.72) { if (pend) { rxChar(pend); pend = ''; } rxChar(c); } else pend = (pend + c).slice(-8); }; }
  let pGate = 0; function mkPsk() { psk = new D.PskRx(G.psk.hz); psk.afc = G.psk.afc; psk.sq = G.psk.sq / 100; psk.onChar = c => { if (performance.now() < pGate || G.psk.sq === 0) rxChar(c); }; }
  /* only print when the waterfall shows a signal right there (a strong neighbour 50 Hz away also 'decodes', as garbage) */
  function pskGate(vals) { const srt = Array.from(vals).sort((a, b) => a - b), med = srt[Math.floor(srt.length * 0.5)]; let mx = -1e9; for (let f = psk.fc - 10; f <= psk.fc + 10; f += 2) mx = Math.max(mx, valAt(f)); if (mx > med + 8 && Math.abs(snapPsk(psk.fc) - psk.fc) < 7) pGate = performance.now() + 2500; }
  /* PSK31 signal browser: a decoder on every signal on the waterfall */
  const BR = []; let brT = 0;
  function brFind(vals) {
    const now = performance.now(); if (now - brT < 1500) return; brT = now; if (!vals) return;
    const [F0, F1] = H.hzRange(), W = vals.length, hz = x => F0 + x / W * (F1 - F0), srt = Array.from(vals).sort((a, b) => a - b), med = srt[Math.floor(W * 0.5)];
    const span = Math.max(2, Math.round(25 / ((F1 - F0) / W))), cand = [];
    for (let x = span; x < W - span; x++) { const v = vals[x]; if (v < med + 12) continue; let top = true; for (let k = -span; k <= span; k++) if (vals[x + k] > v) { top = false; break; } if (top) cand.push([hz(x), v]); }
    cand.sort((a, b) => b[1] - a[1]); const pk = []; for (const [f, v] of cand) if (f > 250 && f < 2750 && !pk.some(q => Math.abs(q - f) < 45)) pk.push(f);
    for (const f0 of pk.slice(0, 12)) { const f = snapPsk(f0); const ch = BR.find(c => Math.abs(c.rx.fc - f) < 40); if (ch) { ch.seen = now; continue; }
      if (BR.length >= 10) { let k = BR.findIndex(c => !c.txt.trim() && now - c.born > 8000); if (k < 0) continue; BR.splice(k, 1); }
      const rx = new D.PskRx(f); rx.sq = Math.max(0.3, G.psk.sq / 100); const c = { rx, txt: '', seen: now, born: now }; rx.onChar = ch2 => { c.txt = (c.txt + (ch2 === '\n' ? ' ' : ch2)).slice(-90); }; BR.push(c); }
    for (let i = BR.length - 1; i >= 0; i--) if (now - BR[i].seen > 30000) BR.splice(i, 1);
    drawBr();
  }
  function drawBr() { if (MODE !== 'PSK31') return; const list = BR.filter(c => c.txt.trim().length > 2).sort((a, b) => b.txt.length - a.txt.length).filter((c, i, A) => !A.slice(0, i).some(o => Math.abs(o.rx.fc - c.rx.fc) < 40)).sort((a, b) => a.rx.fc - b.rx.fc);
    $('dgBr').innerHTML = list.length ? list.map(c => `<div class="dg-bl${Math.abs(c.rx.fc - psk.fc) < 15 ? ' on' : ''}" data-br="${c.rx.fc.toFixed(1)}" role="button" tabindex="0"><b>${Math.round(c.rx.fc)}</b><span>${esc(c.txt.slice(-70))}</span></div>`).join('') : '<div class="f8-empty">Every PSK31 signal on the waterfall gets its own line here. Tap one to read it below.</div>'; }
  $('dgBr').addEventListener('click', e => { const r = e.target.closest('[data-br]'); if (r) pskTune(+r.dataset.br); });
  function pskTune(hz) { G.psk.hz = Math.round(hz * 10) / 10; save(); psk.tune(G.psk.hz); $('dgPHzT').textContent = Math.round(G.psk.hz); H.drawScale(); drawBr(); }
  function rttyTune(c) { G.rtty.center = Math.round(c); save(); rtty.tune(G.rtty.center); $('dgHzT').textContent = G.rtty.center; H.drawScale(); }
  /* tap: RTTY = best mark/space pair near the tap; PSK31 = middle (centroid) of the signal under the tap */
  function valAt(hz) { const v = H.vals(); if (!v) return -200; const [F0, F1] = H.hzRange(), x = Math.round((hz - F0) / (F1 - F0) * v.length); return v[Math.max(0, Math.min(v.length - 1, x))]; }
  function snapRtty(hz) { let best = hz, bv = -1e9; for (let c = hz - 120; c <= hz + 120; c += 2) { const a = valAt(c + G.rtty.shift / 2), b = valAt(c - G.rtty.shift / 2), s = Math.min(a, b) * 2 + a + b; if (s > bv) { bv = s; best = c; } } return best; }
  function snapPsk(hz) { const v = H.vals(); if (!v) return hz; let sw = 0, sx = 0; for (let f = hz - 22; f <= hz + 22; f += 1) { const p = Math.pow(10, valAt(f) / 10); sw += p; sx += p * f; } return sw ? sx / sw : hz; }
  /* RTTY AFC: keep the pair centred */
  let afcT = 0; function rttyAfc() { if (!G.rtty.afc || TXSRC) return; const now = performance.now(); if (now - afcT < 2000) return; afcT = now; if (rtty.q < 0.5) return; const c = snapRtty(G.rtty.center); if (Math.abs(c - G.rtty.center) > 4 && Math.abs(c - G.rtty.center) < 60) rttyTune((c + G.rtty.center) / 2); }
  /* macros (digital: whole lines, sent with a new line before and after) */
  const MAC0 = h => h ? [['CALL', '{THEIR} DE {MY} {MY} K'], ['REPORT', '{THEIR} TU 599 599 {ST} {ST} DE {MY} K'], ['73', 'TU 73 GL {THEIR} DE {MY} SK'], ['AGN', 'AGN AGN DE {MY} K'], ['P2P', '{THEIR} TU 599 599 {ST} P2P {REF} {REF} DE {MY} K'], ['MY CALL', '{MY} {MY}'], ['QRL', 'QRL? DE {MY}'], ['TNX', 'TNX FOR THE PARK 73 DE {MY}']]
    : [['CQ POTA', 'CQ CQ CQ POTA DE {MY} {MY} {MY} {REF} K'], ['REPLY', '{THEIR} DE {MY} TU UR 599 599 {ST} {ST} {THEIR} DE {MY} K'], ['TU QRZ', '{THEIR} TU 73 QRZ DE {MY} POTA K'], ['AGN', 'AGN AGN DE {MY} K'], ['QRZ', 'QRZ? DE {MY} K'], ['P2P', '{THEIR} DE {MY} TU 599 599 {ST} P2P {REF} {REF} K'], ['73', '73 TU {THEIR} DE {MY} SK'], ['MY CALL', '{MY} {MY} K']];
  const macros = () => { const L = H.LG(); return G.mac || MAC0(L ? L.me().hunt : false); };
  function macDraw() { $('dgMac').innerHTML = macros().map((m, i) => `<button type="button" data-dgm="${i}" title="${esc(m[1])}">F${i + 1} ${esc(m[0])}</button>`).join('') + '<button type="button" data-dgmedit>✏️ EDIT</button>'; }
  function sendText(t) {
    t = fill(t).toUpperCase().trim(); if (!t) return; const AC = H.ac();
    if (MODE !== 'RTTY' && MODE !== 'PSK31') return;
    const go = () => { const a = H.ac(), line = '\n' + t + '\n'; const buf = MODE === 'RTTY' ? D.rttyTx(line, G.rtty, a.sampleRate) : D.pskTx(line, G.psk.hz, a.sampleRate);
      txt += '\n[TX] ' + t + '\n'; drawRx(); play(buf, t).then(ok => { if (ok) $('dgTx').placeholder = '▶ sending: ' + t.slice(0, 40); }); };
    if (!AC) H.startAudio().then(ok => ok && go()); else go();
  }
  $('dgMac').addEventListener('click', e => { const b = e.target.closest('[data-dgm]'); if (b) { sendText(macros()[+b.dataset.dgm][1]); return; }
    if (e.target.closest('[data-dgmedit]')) { const M = macros().map(m => m.slice()); for (let i = 0; i < M.length; i++) { const v = prompt(`F${i + 1} ${M[i][0]} (use {MY} {THEIR} {REF} {ST}; blank = keep, RESET = defaults)`, M[i][1]); if (v === null) break; if (v.trim().toUpperCase() === 'RESET') { G.mac = null; save(); macDraw(); return; } if (v.trim()) M[i][1] = v.trim().toUpperCase(); } G.mac = M; save(); macDraw(); } });
  addEventListener('keydown', e => { if (H.root.hidden || (MODE !== 'RTTY' && MODE !== 'PSK31') || !/^F[1-8]$/.test(e.key)) return; e.preventDefault(); const m = macros()[+e.key.slice(1) - 1]; if (m) sendText(m[1]); });
  $('dgTx').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); const v = $('dgTx').value; $('dgTx').value = ''; sendText(v); } });
  $('dgSendT').onclick = () => { const v = $('dgTx').value; $('dgTx').value = ''; sendText(v); };
  $('dgStop').onclick = () => { stopTx(); $('dgTx').placeholder = 'Type here and press Enter to send it'; };
  $('dgClr').onclick = () => { txt = ''; drawRx(); calls = []; $('dgCalls').innerHTML = ''; };
  $('dgShift').value = String(G.rtty.shift); $('dgShift').onchange = () => { G.rtty.shift = +$('dgShift').value; save(); rtty.set({ shift: G.rtty.shift }); H.drawScale(); };
  $('dgBaud').value = String(G.rtty.baud); $('dgBaud').onchange = () => { G.rtty.baud = +$('dgBaud').value; save(); rtty.set({ baud: G.rtty.baud }); };
  $('dgRev').checked = G.rtty.rev; $('dgRev').onchange = () => { G.rtty.rev = $('dgRev').checked; save(); rtty.set({ rev: G.rtty.rev }); H.drawScale(); };
  $('dgAfc').onchange = () => { if (MODE === 'PSK31') { G.psk.afc = $('dgAfc').checked; psk.afc = G.psk.afc; } else { G.rtty.afc = $('dgAfc').checked; } save(); };
  $('dgSq').value = G.psk.sq; $('dgSq').oninput = () => { G.psk.sq = +$('dgSq').value; psk.sq = G.psk.sq / 100; save(); };
  $('dgCall').oninput = e => { e.target.value = e.target.value.toUpperCase().replace(/\s/g, ''); };
  $('dgLog').onclick = () => { const L = H.LG(), call = $('dgCall').value.trim().toUpperCase(); if (!L || !call) { H.note('Type or tap their call first.'); return; }
    const mode = MODE === 'SSTV' ? 'SSTV' : MODE; const k = H.dialK() + (MODE === 'SSTV' ? 0 : audioHz() / 1000);
    const r = L.add({ call, khz: Math.round(k * 10) / 10, mode, rs: $('dgRs').value || (MODE === 'SSTV' ? '595' : '599'), rr: $('dgRr').value || (MODE === 'SSTV' ? '595' : '599'), ref: $('dgRef').value.trim() });
    if (r && r.ok) { H.note(`✅ ${call} logged · ${S.band} ${mode}${r.n ? ' · ' + r.n + (L.me().hunt ? ' today' : ' this activation') : ''}`, 3000, 'log'); $('dgCall').value = ''; $('dgRef').value = ''; } else H.note('⚠️ Not logged: ' + ((r && r.msg) || ''), 5000); };

  /* ---------------- SSTV ---------------- */
  const sstv = new D.SstvRx(); let cur = null, rows = 0;
  const cv = $('dgCv'), cx = cv.getContext('2d');
  function blank() { cx.fillStyle = '#0b0805'; cx.fillRect(0, 0, cv.width, cv.height); cx.fillStyle = '#6b5a3a'; cx.font = '14px Arial'; cx.textAlign = 'center'; cx.fillText('SSTV pictures show up here', cv.width / 2, cv.height / 2); }
  blank();
  sstv.auto = G.sstv.auto;
  sstv.onStart = m => { cur = m; rows = 0; cv.width = m.w; cv.height = m.h; cx.fillStyle = '#000'; cx.fillRect(0, 0, m.w, m.h); $('dgSst').textContent = '📺 Receiving ' + m.name + '…'; H.chime(); };
  sstv.onRow = (y, px) => { if (!cur || y >= cur.h) return; const id = cx.createImageData(cur.w, 1); id.data.set(px); cx.putImageData(id, 0, y); rows = Math.max(rows, y + 1); if (y % 8 === 0) $('dgSst').textContent = `📺 ${cur.name} · line ${y + 1} of ${cur.h}`; };
  sstv.onEnd = (m, r) => { $('dgSst').textContent = r > 20 ? `✅ ${m.name} picture done (${r} lines). Waiting for the next one…` : 'Waiting for a picture…'; if (r > 20) galAdd(m.name); cur = null; };
  const GAL = [];
  function galAdd(name) { try { const url = cv.toDataURL('image/jpeg', 0.85); GAL.unshift({ url, name, t: H.nowS() }); if (GAL.length > 12) GAL.pop(); galDraw(); idbPut(); } catch (e) {} }
  function galDraw() { $('dgGal').innerHTML = GAL.map((g, i) => `<button type="button" data-gal="${i}" title="${esc(g.name)} · ${H.utc(g.t)}z"><img src="${g.url}" alt="SSTV picture ${i + 1}"><small>${H.utc(g.t).replace(/(\d\d)(\d\d)/, '$1:$2')}z</small></button>`).join(''); }
  $('dgGal').addEventListener('click', e => { const b = e.target.closest('[data-gal]'); if (!b) return; const g = GAL[+b.dataset.gal], im = new Image(); im.onload = () => { cv.width = im.width; cv.height = im.height; cx.drawImage(im, 0, 0); }; im.src = g.url; });
  /* keep the last 12 pictures on this device (IndexedDB) */
  function idb() { return new Promise((ok, no) => { try { const r = indexedDB.open('kpc-sstv', 1); r.onupgradeneeded = () => r.result.createObjectStore('kv'); r.onsuccess = () => ok(r.result); r.onerror = no; } catch (e) { no(e); } }); }
  function idbPut() { idb().then(db => { db.transaction('kv', 'readwrite').objectStore('kv').put(GAL, 'gal'); }).catch(() => {}); }
  idb().then(db => { const q = db.transaction('kv').objectStore('kv').get('gal'); q.onsuccess = () => { if (Array.isArray(q.result)) { GAL.push(...q.result.slice(0, 12)); galDraw(); } }; }).catch(() => {});
  const fname = () => 'KPC-SSTV-' + new Date().toISOString().slice(0, 16).replace(/[-:T]/g, '') + '.png';
  $('dgSave').onclick = () => { cv.toBlob(b => { if (!b) return; const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = fname(); document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); }, 'image/png'); };
  $('dgShare').onclick = () => { cv.toBlob(async b => { if (!b) return; const f = new File([b], fname(), { type: 'image/png' }); if (navigator.canShare && navigator.canShare({ files: [f] })) { try { await navigator.share({ files: [f], title: 'SSTV picture' }); } catch (e) {} } else $('dgSave').onclick(); }, 'image/png'); };
  $('dgAuto').checked = G.sstv.auto; $('dgAuto').onchange = () => { G.sstv.auto = $('dgAuto').checked; sstv.auto = G.sstv.auto; save(); };
  $('dgMan').onchange = () => { G.sstv.man = $('dgMan').value; save(); };
  $('dgGo').onclick = () => { if (!H.running()) { H.startAudio(); } sstv.stop(); sstv.manual($('dgMan').value); };
  $('dgStopRx').onclick = () => sstv.stop();
  /* sending: a photo or a KPC card, with text on it */
  const tc = $('dgTxCv'), tx = tc.getContext('2d'); let PIC = null;
  function txSize() { const m = D.SSTV[G.sstv.tx]; tc.width = m.w; tc.height = m.h; $('dgTxLen').textContent = Math.round(m.secs + 1) + ' seconds on the air'; }
  function txDraw() {
    txSize(); const W = tc.width, Hh = tc.height;
    if (PIC) { const r = Math.max(W / PIC.width, Hh / PIC.height), w = PIC.width * r, h = PIC.height * r; tx.drawImage(PIC, (W - w) / 2, (Hh - h) / 2, w, h); }
    else { const g = tx.createLinearGradient(0, 0, W, Hh); g.addColorStop(0, '#1b2a1a'); g.addColorStop(1, '#5a3a12'); tx.fillStyle = g; tx.fillRect(0, 0, W, Hh); tx.fillStyle = '#f0c96b'; tx.font = `900 ${Math.round(Hh * 0.2)}px Arial`; tx.textAlign = 'center'; tx.fillText(me() || 'K4TEST', W / 2, Hh * 0.56); tx.font = `700 ${Math.round(Hh * 0.07)}px Arial`; tx.fillStyle = '#fff'; tx.fillText([myRef(), H.myGrid()].filter(Boolean).join(' · ') || 'KENTUCKY PORTABLE CLUB', W / 2, Hh * 0.72); if (LOGO.complete && LOGO.naturalWidth) { const s = Hh * 0.28; tx.drawImage(LOGO, W / 2 - s / 2, Hh * 0.08, s, s); } }
    const band = (t, y) => { t = fill(t).toUpperCase().trim(); if (!t) return; const fs = Math.round(Hh * 0.085); tx.font = `900 ${fs}px Arial`; tx.textAlign = 'center'; tx.fillStyle = 'rgba(0,0,0,.6)'; tx.fillRect(0, y - fs * 1.05, W, fs * 1.4); tx.fillStyle = '#fff'; tx.fillText(t, W / 2, y); };
    band($('dgTop').value, Math.round(Hh * 0.11)); band($('dgBot').value, Math.round(Hh * 0.96));
  }
  const LOGO = new Image(); LOGO.onload = () => { if (!PIC) txDraw(); }; LOGO.src = 'KPC-logo.png';
  $('dgTxMode').value = G.sstv.tx; $('dgTxMode').onchange = () => { G.sstv.tx = $('dgTxMode').value; save(); txDraw(); };
  $('dgTop').value = G.sstv.top; $('dgBot').value = G.sstv.bot; ['dgTop', 'dgBot'].forEach(id => $(id).oninput = () => { G.sstv.top = $('dgTop').value; G.sstv.bot = $('dgBot').value; save(); txDraw(); });
  $('dgPick').onclick = () => $('dgFile').click(); $('dgCard').onclick = () => { PIC = null; txDraw(); };
  $('dgFile').onchange = () => { const f = $('dgFile').files[0]; if (!f) return; const im = new Image(); im.onload = () => { PIC = im; txDraw(); }; im.src = URL.createObjectURL(f); };
  $('dgSend').addEventListener('toggle', () => { if ($('dgSend').open) txDraw(); });
  let txTimer = null;
  $('dgTxGo').onclick = async () => { if (!H.ac() && !(await H.startAudio())) return; txDraw(); const AC = H.ac(), m = D.SSTV[G.sstv.tx]; const img = tx.getImageData(0, 0, m.w, m.h);
    $('dgTxT').textContent = 'Making the sound…'; await new Promise(r => setTimeout(r, 30)); const buf = D.sstvTx(img, G.sstv.tx, AC.sampleRate); const t0 = H.nowS();
    const ok = await play(buf, 'SSTV', () => { clearInterval(txTimer); $('dgTxT').textContent = '✅ Sent.'; }); if (!ok) { $('dgTxT').textContent = ''; return; }
    clearInterval(txTimer); txTimer = setInterval(() => { const s = Math.max(0, Math.round(buf.length / AC.sampleRate - (H.nowS() - t0))); $('dgTxT').textContent = `📡 Sending ${G.sstv.tx}… ${s} s left`; if (!TXSRC) clearInterval(txTimer); }, 500); };
  $('dgTxStop').onclick = () => { stopTx(); clearInterval(txTimer); $('dgTxT').textContent = 'Stopped.'; };

  /* ---------------- WSPR ---------------- */
  let W = null, WK = null, wid = 0, wNext = false, wTxCyc = -1, wTxOn = -1, WLINES = [], WHO = [];
  const cyc = t => Math.floor(t / 120) * 120;
  function wNew(c) { W = { c, buf: new Float32Array(114 * R), got: new Uint8Array(114), tx: false }; }
  function wFeed(blk, t) {
    const c = cyc(t); if (!W || c > W.c + 119) { if (W && !W.done) wEnd(); wNew(c); }
    for (let i = 0; i < blk.length; i++) { const tt = t + i / R - W.c; if (tt < 0) continue; if (tt >= 114) { if (!W.done) wEnd(); const c2 = cyc(t + i / R); if (c2 > W.c) { wNew(c2); } continue; } const k = Math.floor(tt * R); W.buf[k] = blk[i]; W.got[Math.floor(tt)] = 1; }
  }
  function wEnd() {
    W.done = true; const n = W.got.reduce((a, b) => a + b, 0); if (W.tx || W.c === wTxOn || n < 70) { if (MODE === 'WSPR') $('dgWSt').textContent = (W.tx || W.c === wTxOn) ? 'Sent my beacon this cycle.' : 'Listening… (first full cycle starts on the next even minute)'; return; }
    const c = W.c, audio = W.buf; if (window.__wsprKeep) window.__wsprLast = { c, n, audio: audio.slice() }; $('dgWSt').textContent = '🔎 Decoding ' + H.utc(c).replace(/(\d\d)(\d\d)/, '$1:$2') + 'z…';
    const done = res => { wShow(c, res); };
    try { if (!WK) { WK = new Worker('kpc-digi.js?v=20261018b'); WK.onmessage = e => { const m = e.data; if (m && m.cmd === 'wspr' && WK.cb && WK.cb[m.id]) { WK.cb[m.id](m.res || []); delete WK.cb[m.id]; } }; WK.cb = {}; }
      const id = ++wid; WK.cb[id] = done; WK.postMessage({ cmd: 'wspr', id, audio, opt: { ms: 60000 } }, [audio.buffer]); }
    catch (e) { setTimeout(() => { try { done(D.wsprDecode(audio, { ms: 30000 })); } catch (x) { done([]); } }, 50); }
  }
  function wShow(c, res) {
    const my = H.g2ll(H.myGrid()), dial = H.dialK();
    for (const r of res) { const ll = r.grid ? H.g2ll(r.grid) : null, d = my && ll ? H.distB(my, ll) : null; WLINES.push({ t: c, snr: r.snr, dt: r.dt, mhz: (dial * 1000 + 1500 + r.df) / 1e6, drift: r.drift, call: r.call, grid: r.grid, dbm: r.dbm, d }); }
    if (WLINES.length > 300) WLINES = WLINES.slice(-300);
    if (MODE === 'WSPR') $('dgWSt').textContent = `${res.length} decoded at ${H.utc(c).replace(/(\d\d)(\d\d)/, '$1:$2')}z`;
    wDraw(); if (H.mapOpen()) wMap();
  }
  function wDraw() { const el = $('dgWList'); if (!WLINES.length) return; const L = WLINES.slice(-120);
    let last = -1; el.innerHTML = L.map(x => { const sep = x.t !== last ? `<div class="f8-sep">${H.utc(x.t).replace(/(\d\d)(\d\d)/, '$1:$2')}z ── WSPR</div>` : ''; last = x.t;
      return sep + `<div class="f8-l dg-wr"><span class="db">${x.snr}</span><span class="dt">${x.dt.toFixed(1)}</span><span class="hz">${x.mhz.toFixed(6)}</span><span class="tx"><b>${esc(x.call)}</b> ${esc(x.grid)} ${x.dbm} dBm${x.drift ? ' · drift ' + x.drift : ''}${x.d ? ` <small>${x.d.mi.toLocaleString()} mi ${x.d.c}</small>` : ''}</span></div>`; }).join('');
    el.scrollTop = el.scrollHeight; }
  function wMap() { const now = H.nowS(), seen = {}, hear = []; for (let i = WLINES.length - 1; i >= 0; i--) { const x = WLINES[i]; if (now - x.t > 3600 || seen[x.call] || !x.grid) continue; seen[x.call] = 1; hear.push({ call: x.call, grid: x.grid, snr: x.snr }); }
    H.map(hear, WHO.map(w => ({ call: w.rx, grid: w.loc, snr: w.snr }))); }
  function wMsg() { const c = me(), g = H.myGrid().slice(0, 4), sym = c && g ? D.wsprEncode(c, g, G.wspr.dbm) : null;
    $('dgWMsg').innerHTML = sym ? `Sends: <b>${esc(c)} ${esc(g)} ${G.wspr.dbm}</b>` : `<span class="bad">${!c ? 'Put your call in ⚙ STATION.' : !g ? 'Put your grid in ⚙ STATION.' : 'WSPR can only send a plain call (up to 6 characters, no /P).'}</span>`; return sym; }
  function wTick() {
    const t = H.nowS(), c = cyc(t), into = t - c; $('dgWNext').textContent = String(Math.floor((120 - into) / 60)) + ':' + String(Math.floor((120 - into) % 60)).padStart(2, '0');
    if (MODE !== 'WSPR' || !H.running()) return;
    /* transmit? decide once per cycle, start 1 s after the even minute */
    if (into < 0.9 && wTxCyc !== c) { wTxCyc = c; const want = G.wspr.tx && (wNext || Math.random() * 100 < G.wspr.pct); wNext = false;
      if (want) { const sym = wMsg(); if (sym && !TXSRC) { const AC = H.ac(), buf = D.wsprTx(sym, G.wspr.hz, AC.sampleRate); wTxOn = c; if (W && W.c === c) W.tx = true;
        setTimeout(() => { play(buf, 'WSPR', () => { $('dgWSt').textContent = 'Beacon sent. Listening…'; }).then(ok => { if (ok) $('dgWSt').textContent = `📡 Sending my beacon (${me()} ${H.myGrid().slice(0, 4)} ${G.wspr.dbm}) at ${G.wspr.hz} Hz…`; }); }, Math.max(0, (1 - into) * 1000)); } } }
  }
  setInterval(wTick, 250);
  $('dgWTx').checked = G.wspr.tx; $('dgWTx').onchange = () => { G.wspr.tx = $('dgWTx').checked; save(); wMsg(); };
  $('dgWPct').value = String(G.wspr.pct); $('dgWPct').onchange = () => { G.wspr.pct = +$('dgWPct').value; save(); };
  $('dgWDbm').value = String(G.wspr.dbm); $('dgWDbm').onchange = () => { G.wspr.dbm = +$('dgWDbm').value; save(); wMsg(); };
  $('dgWHz').value = G.wspr.hz; $('dgWHz').onchange = () => { G.wspr.hz = Math.max(1410, Math.min(1590, +$('dgWHz').value || 1500)); $('dgWHz').value = G.wspr.hz; save(); H.drawScale(); };
  $('dgWNow').onclick = () => { if (!wMsg()) return; if (!G.wspr.tx) { G.wspr.tx = true; $('dgWTx').checked = true; save(); } wNext = true; if (!H.running()) H.startAudio(); H.note('Your beacon goes out at the start of the next even minute.', 3000); };
  $('dgWho').onclick = () => { const c = me(); if (!c) { H.note('Put your call in ⚙ STATION first.'); return; } $('dgWhoT').textContent = 'Asking wspr.live…';
    const sql = `SELECT time, rx_sign, rx_loc, snr, frequency FROM wspr.rx WHERE tx_sign='${c.replace(/[^A-Z0-9/]/g, '')}' AND time > now() - INTERVAL 60 MINUTE ORDER BY time DESC LIMIT 200 FORMAT JSON`;
    fetch('https://db1.wspr.live/?query=' + encodeURIComponent(sql)).then(r => r.json()).then(j => { const rows = (j && j.data) || [], my = H.g2ll(H.myGrid());
      WHO = rows.map(r => ({ rx: r.rx_sign, loc: r.rx_loc, snr: +r.snr, t: r.time })); const seen = {};
      const L = WHO.filter(w => !seen[w.rx] && (seen[w.rx] = 1)).map(w => { const ll = H.g2ll(w.loc), d = my && ll ? H.distB(my, ll) : null; return { ...w, d }; }).sort((a, b) => (b.d ? b.d.mi : 0) - (a.d ? a.d.mi : 0));
      $('dgWhoT').textContent = L.length ? `${L.length} station${L.length > 1 ? 's' : ''} heard you${L[0].d ? ' · farthest ' + L[0].d.mi.toLocaleString() + ' mi' : ''}` : 'Nobody reported you in the last hour (it can take a few minutes to show up).';
      $('dgWhoL').hidden = !L.length; $('dgWhoL').innerHTML = L.map(w => `<div class="f8-l"><span class="db">${w.snr}</span><span class="tx"><b>${esc(w.rx)}</b> ${esc(w.loc)}${w.d ? ` <small>${w.d.mi.toLocaleString()} mi ${w.d.c}</small>` : ''} · ${esc(String(w.t).slice(11, 16))}z</span></div>`).join(''); wMap(); })
      .catch(() => { $('dgWhoT').textContent = 'wspr.live did not answer (no signal?).'; }); };

  /* ---------------- hooks for the FT8 screen ---------------- */
  let qT = 0;
  window.KPCDigiUI = {
    mode(m) { const was = MODE; MODE = /^(RTTY|PSK31|SSTV|WSPR)$/.test(m) ? m : ''; if (was && was !== MODE) stopTx(); if (MODE !== 'SSTV' && sstv.img) sstv.stop();
      if (!MODE) return; $('dgName').textContent = MODE; $('dgAfc').checked = MODE === 'PSK31' ? G.psk.afc : G.rtty.afc;
      $('dgRs').value = MODE === 'SSTV' ? '595' : '599'; $('dgRr').value = MODE === 'SSTV' ? '595' : '599'; $('dgHzT').textContent = G.rtty.center; $('dgPHzT').textContent = Math.round(G.psk.hz);
      if (MODE === 'WSPR') wMsg(); if (MODE === 'PSK31') drawBr(); },
    range() { return MODE === 'SSTV' ? [1000, 2500] : MODE === 'WSPR' ? [1400, 1600] : [200, 2800]; },
    feed(blk, t) {
      if (MODE === 'RTTY') { for (let i = 0; i < blk.length; i++) rtty.feed(blk[i]); rttyAfc(); }
      else if (MODE === 'PSK31') { for (let i = 0; i < blk.length; i++) { const x = blk[i]; psk.feed(x); for (const c of BR) c.rx.feed(x); } }
      else if (MODE === 'SSTV') { if (!TXSRC) for (let i = 0; i < blk.length; i++) sstv.feed(blk[i]); }
      else if (MODE === 'WSPR') wFeed(blk, t);
      const now = performance.now(); if (now - qT > 200) { qT = now; const q = MODE === 'RTTY' ? rtty.q : MODE === 'PSK31' ? Math.max(0, psk.q) : 0; $('dgQ').style.width = Math.round(q * 100) + '%'; if (MODE === 'PSK31' && G.psk.afc) $('dgPHzT').textContent = Math.round(psk.fc); }
    },
    wf(vals) { if (MODE === 'PSK31') { pskGate(vals); brFind(vals); } },
    marks(m) {
      if (MODE === 'RTTY') { const s = G.rtty.shift / 2; m(G.rtty.center + s, 8, G.rtty.rev ? '#ff5c5c' : '#45e08f', 5); m(G.rtty.center - s, 8, G.rtty.rev ? '#45e08f' : '#ff5c5c', 5); }
      else if (MODE === 'PSK31') { m(psk ? psk.fc : G.psk.hz, 31, '#45e08f', 5); for (const c of BR) m(c.rx.fc, 3, '#f0c96b', 3); }
      else if (MODE === 'SSTV') { m(1200, 6, '#ff5c5c', 4); m(1500, 6, '#c9b48a', 4); m(1900, 6, '#4da3ff', 4); m(2300, 6, '#fff', 4); }
      else if (MODE === 'WSPR') { m(1500, 200, 'rgba(240,201,107,.25)', 3); m(G.wspr.hz, 6, '#ff5c5c', 5); }
    },
    click(hz) { if (MODE === 'RTTY') rttyTune(snapRtty(hz)); else if (MODE === 'PSK31') pskTune(snapPsk(hz)); else if (MODE === 'WSPR') { G.wspr.hz = Math.max(1410, Math.min(1590, Math.round(hz))); $('dgWHz').value = G.wspr.hz; save(); H.drawScale(); } },
    go(o, off) { if (o.call) { $('dgCall').value = String(o.call).toUpperCase(); } if (o.ref) $('dgRef').value = o.ref; if (off != null && off > 200 && off < 2800) { if (MODE === 'RTTY') rttyTune(off); else if (MODE === 'PSK31') pskTune(off); }
      H.note(`Listening for ${o.call || 'them'}${o.ref ? ' at ' + o.ref : ''}. Tap their signal on the waterfall if it isn't lined up${H.running() ? '' : ' (press START LISTENING first)'}.`, 6000); },
    mapOpen() { wMap(); },
    debug: () => ({ br: BR.map(c => [Math.round(c.rx.fc), c.rx.q.toFixed(2), c.txt]), psk: psk && [psk.fc, psk.q], rtty: rtty && rtty.q })
  };
  mkRtty(); mkPsk(); macDraw(); txSize();
  H.refresh && (H.refresh(), 0);
})();
