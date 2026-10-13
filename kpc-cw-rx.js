/* KPC CW Practice — "Listen & Decode": decode CW from the microphone or from another browser tab (a WebSDR).
   Goertzel tone detector on the chosen pitch, adaptive threshold with a noise squelch, and dit/dah timing that
   learns the sender's speed (2-means on recent mark lengths). Needs kpc-cw.js (uses its Morse table and timing). */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const K = () => window.KPCCW;

let ctx = null, stream = null, srcNode = null, proc = null, an = null, sink = null, testOsc = null, testGain = null, testNoise = null;
let running = false, raf = 0, fs = 48000, sampleT = 0, autoTimer = 0;

/* ---------------- tone detector ---------------- */
const N = 384, HOP = 128;
let ring = new Float32Array(N), rpos = 0, hopCnt = 0, win = new Float32Array(N), coeff = 0;
for (let i = 0; i < N; i++) win[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (N - 1));
let freq = 600, auto = true;
function setFreq(f) {
  freq = Math.max(200, Math.min(1500, f));
  coeff = 2 * Math.cos(2 * Math.PI * freq / fs);
  const o = $('rxFreq'); if (o) o.textContent = Math.round(freq) + ' Hz';
}
function goertzel() {
  let s1 = 0, s2 = 0;
  for (let i = 0; i < N; i++) { const x = ring[(rpos + i) % N] * win[i]; const s0 = x + coeff * s1 - s2; s2 = s1; s1 = s0; }
  return Math.sqrt(Math.max(0, s1 * s1 + s2 * s2 - coeff * s1 * s2));
}

/* ---------------- envelope -> marks/spaces ---------------- */
let es = 0, sig = 0, noise = 0, inited = false, state = false, cand = false, candT = 0, holdN = 0, segT = 0;
let marks = [], ditMs = 1200 / 18, cur = [], wordDone = true, text = '', lastEdge = 0, snrDb = 0, warmUntil = 0;
function resetDecoder() {
  es = 0; sig = 0; noise = 0; inited = false; state = false; cand = false; holdN = 0; segT = sampleT / fs;
  marks = []; cur = []; wordDone = true; warmUntil = sampleT / fs + 0.4;
  ditMs = 1200 / ((K() && K().S.wpm) || 18);
}
function thresholdMs() {
  // two clusters (dits and dahs) from recent marks; fall back to the current speed guess
  const ms = marks.filter(m => m < 700);           // ignore carriers / tune-ups
  if (ms.length >= 4) {
    let a = Math.min(...ms), b = Math.max(...ms);
    if (b / a > 1.8) {
      for (let it = 0; it < 6; it++) {
        const t = Math.sqrt(a * b), lo = ms.filter(m => m < t), hi = ms.filter(m => m >= t);
        if (!lo.length || !hi.length) break;
        a = lo.reduce((x, y) => x + y, 0) / lo.length; b = hi.reduce((x, y) => x + y, 0) / hi.length;
      }
      if (b / a > 1.8) { ditMs = Math.max(20, Math.min(240, (a + b / 3) / 2)); return Math.sqrt(a * b); }
    }
  }
  return ditMs * 2;
}
function onMarkEnd(ms) {
  if (ms < 8) return;
  marks.push(ms); if (marks.length > 24) marks.shift();
  cur.push(ms); if (cur.length > 8) cur.shift();
  // keep the speed estimate current so letter and word gaps are judged right
  if (ms < ditMs * 0.75 && ms >= 15) ditMs = ms * 1.05;   // shorter than our dit: they're sending faster
  thresholdMs();                                          // refines ditMs once dits and dahs have both been heard
}
function emit(s) {
  text += s; if (text.length > 4000) text = text.slice(-3000);
  const box = $('rxText'); if (box) { box.textContent = text; box.scrollTop = box.scrollHeight; }
  if (copyTest.on) copyTest.got += s;
}
/* dits vs dahs are decided when the letter is finished, using everything heard so far (including this letter) */
function endChar() {
  if (!cur.length) return;
  const thr = thresholdMs(), code = cur.map(m => m < thr ? '.' : '-').join('');
  const d = K() ? K().decode(code) : null;
  emit(d || '*'); cur = []; wordDone = false;
}
function hop(e, tSec) {
  const dt = HOP / fs;
  es = es * 0.4 + e * 0.6;
  if (!inited) { if (es <= 0) return; noise = es; sig = 0; inited = true; }
  const warm = tSec < warmUntil;
  // signal level: follows the tone while it's on, fades slowly between marks
  if (state) sig += (es - sig) * Math.min(1, dt / 0.04); else sig *= Math.exp(-dt / 4);
  // trigger: at least ~3.5x the average noise (noise alone almost never gets there), or halfway to the signal level
  const hi = Math.max(noise * 3.5, noise + (sig - noise) * 0.5), lo = Math.max(noise * 2.4, noise + (sig - noise) * 0.33);
  if (!state && (es < hi || warm)) noise += (es - noise) * Math.min(1, dt / (warm ? 0.05 : 0.5));   // noise: average between marks (learns fast at the start)
  snrDb = sig > noise ? 20 * Math.log10(sig / (noise + 1e-12)) : 0;
  const raw = state ? es > lo : es > hi;
  // debounce: a change must hold for ~20% of a dit
  const need = Math.max(2, Math.round(0.2 * ditMs / 1000 / dt));
  if (raw !== state) { if (cand !== raw) { cand = raw; candT = tSec; holdN = 0; } holdN++; }
  else { cand = state; holdN = 0; }
  if (raw !== state && holdN >= need) {
    const ms = (candT - segT) * 1000;
    if (state && candT > warmUntil) onMarkEnd(ms);
    state = raw; segT = candT; lastEdge = candT; holdN = 0;
    lamp(state);
  }
  if (!state && cur.length) {
    const gap = (tSec - segT) * 1000;
    if (gap > ditMs * 2.2) endChar();
  }
  if (!state && !wordDone && !cur.length) {
    const gap = (tSec - segT) * 1000;
    if (gap > ditMs * 5.2) { emit(' '); wordDone = true; }
  }
}
/* after a retune, drop the half-heard letter and let the levels settle again */
function retuned() { state = false; cand = false; holdN = 0; cur = []; segT = sampleT / fs; noise = es; sig = 0; warmUntil = sampleT / fs + 0.08; lamp(false); }
function lamp(on) { const l = $('rxLamp'); if (l) l.classList.toggle('on', on); }

/* ---------------- audio graph ---------------- */
function graph(source, hear) {
  ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
  if (ctx.state === 'suspended') ctx.resume();
  fs = ctx.sampleRate; setFreq(freq);
  srcNode = source;
  an = ctx.createAnalyser(); an.fftSize = 4096; an.smoothingTimeConstant = 0.5; an.minDecibels = -110; an.maxDecibels = -30;
  proc = ctx.createScriptProcessor(1024, 1, 1);
  sink = ctx.createGain(); sink.gain.value = 0;
  proc.onaudioprocess = ev => {
    const x = ev.inputBuffer.getChannelData(0);
    for (let i = 0; i < x.length; i++) {
      ring[rpos] = x[i]; rpos = (rpos + 1) % N; sampleT++;
      if (++hopCnt === HOP) { hopCnt = 0; hop(goertzel(), sampleT / fs); }
    }
  };
  srcNode.connect(an); srcNode.connect(proc); proc.connect(sink); sink.connect(ctx.destination);
  if (hear) { const g = ctx.createGain(); g.gain.value = (K() && K().S.vol) || 0.6; srcNode.connect(g); g.connect(ctx.destination); hear.g = g; }
  running = true; resetDecoder();
  ui(true); waterfall(); autoTimer = setInterval(autoTune, 150);
}
function stop() {
  running = false; cancelAnimationFrame(raf); clearInterval(autoTimer);
  try { if (proc) { proc.disconnect(); proc.onaudioprocess = null; } if (srcNode) srcNode.disconnect(); if (an) an.disconnect(); } catch (e) {}
  if (stream) stream.getTracks().forEach(t => t.stop()); stream = null;
  try { if (testOsc) testOsc.stop(); if (testNoise) testNoise.stop(); } catch (e) {} testOsc = testNoise = null;
  endChar(); lamp(false); ui(false);
}
async function useMic() {
  stop(); msg('');
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } });
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    graph(ctx.createMediaStreamSource(stream));
    msg('Listening through the microphone. Hold the phone near the speaker, turn the volume up, keep the room quiet.');
  } catch (e) { msg('The microphone was blocked. Allow it for this site and try again.'); }
}
async function useTab() {
  stop(); msg('');
  try {
    stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false }, selfBrowserSurface: 'exclude', systemAudio: 'include', preferCurrentTab: false });
    if (!stream.getAudioTracks().length) { stream.getTracks().forEach(t => t.stop()); stream = null; msg('No sound was shared. Pick the WebSDR tab and turn on "Share tab audio".'); return; }
    stream.getVideoTracks().forEach(t => { t.enabled = false; });
    stream.getAudioTracks()[0].addEventListener('ended', stop);
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
    graph(ctx.createMediaStreamSource(new MediaStream(stream.getAudioTracks())));
    msg('Decoding the shared tab. Tune the WebSDR to a CW signal — you\'ll keep hearing it from that tab.');
  } catch (e) { msg('Tab sharing was cancelled or isn\'t supported in this browser.'); }
}
/* built-in practice signal, so you can see how it works without a radio */
const SAMPLES = ['CQ POTA CQ POTA DE W4KPC W4KPC K', 'KZ4CP GM UR 5NN 5NN KY KY BK', 'CQ SOTA DE N4XX/P K', 'TU 73 E E', 'BK TU UR 579 579 TN TN BK', 'CQ CQ DE K4ZSR K4ZSR K'];
function useTest(opts) {
  stop(); msg('');
  ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
  const o = opts || {};
  const wpm = o.wpm || (14 + Math.floor(Math.random() * 12)), txt = o.text || SAMPLES[Math.floor(Math.random() * SAMPLES.length)];
  const pitch = o.pitch || 550 + Math.floor(Math.random() * 300);
  const mix = ctx.createGain();
  testOsc = ctx.createOscillator(); testOsc.frequency.value = pitch;
  testGain = ctx.createGain(); testGain.gain.value = 0;
  testOsc.connect(testGain); testGain.connect(mix);
  const nb = ctx.createBuffer(1, ctx.sampleRate * 2, ctx.sampleRate), d = nb.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1);
  testNoise = ctx.createBufferSource(); testNoise.buffer = nb; testNoise.loop = true;
  const ng = ctx.createGain(); ng.gain.value = o.noise != null ? o.noise : 0.04; testNoise.connect(ng); ng.connect(mix);
  const tl = K().timeline(txt, wpm, wpm, o.jitter != null ? o.jitter : 0.05), t0 = ctx.currentTime + 1.0, g = testGain.gain;
  tl.marks.forEach(m => { g.setTargetAtTime(0.5, t0 + m[0], 0.002); g.setTargetAtTime(0, t0 + m[1], 0.002); });
  testOsc.start(); testNoise.start();
  const hear = {}; graph(mix, o.silent ? null : hear);
  if (!o.hunt) setFreq(pitch);   // we know where the practice signal is
  msg(`Practice signal: ${wpm} WPM at ${pitch} Hz. Try to copy it, then compare with the decoder.`);
  const endMs = (tl.total + 1.9) * 1000;
  setTimeout(() => { if (testOsc) { endChar(); msg('Practice signal finished. Press it again for another one.'); stop(); } }, endMs);
  return { wpm, txt, pitch, endMs };
}

/* ---------------- auto-tune + waterfall ---------------- */
let spec = null, bins = null;
function autoTune() {
  if (!running || !an) return;
  bins = bins || new Float32Array(an.frequencyBinCount); an.getFloatFrequencyData(bins);
  spec = spec || new Float32Array(an.frequencyBinCount);
  for (let i = 0; i < bins.length; i++) spec[i] = spec[i] * 0.5 + (isFinite(bins[i]) ? bins[i] : -140) * 0.5;
  if (!auto) return;
  const hz = fs / an.fftSize, lo = Math.floor(250 / hz), hi = Math.ceil(1300 / hz);
  let best = lo; for (let i = lo; i <= hi; i++) if (spec[i] > spec[best]) best = i;
  const sorted = Array.from(spec.slice(lo, hi + 1)).sort((x, y) => x - y), med = sorted[sorted.length >> 1];
  if (spec[best] < med + 15) return;               // nothing clearly above the noise — stay put
  const c0 = Math.round(freq / hz);
  const idle = !state && !cur.length;
  if (Math.abs(best - c0) > 1 && spec[best] > (spec[c0] || -140) + 6 && (idle || spec[c0] < spec[best] - 15)) {
    const a = spec[best - 1], b = spec[best], c = spec[best + 1], p = 0.5 * (a - c) / (a - 2 * b + c || 1);
    setFreq((best + (isFinite(p) ? p : 0)) * hz);
    retuned();
  }
}
const F0 = 200, F1 = 1300;
function waterfall() {
  const cv = $('rxWf'); if (!cv || !an) return;
  const g = cv.getContext('2d'), W = cv.width, H = cv.height;
  const data = new Uint8Array(an.frequencyBinCount), hz = fs / an.fftSize, row = g.createImageData(W, 1);
  const col = v => { // dark → blue → cyan → yellow → white
    const t = v / 255; const r = Math.min(255, Math.max(0, (t - 0.55) * 4 * 255)), gg = Math.min(255, Math.max(0, (t - 0.25) * 2.2 * 255)), b = Math.min(255, Math.max(0, t < 0.5 ? t * 2 * 255 : (1 - t) * 2.2 * 255 + 60));
    return [r, gg, b];
  };
  let skip = 0;
  const step = () => {
    if (!running) return;
    raf = requestAnimationFrame(step);
    if ((skip = (skip + 1) % 2)) return;
    an.getByteFrequencyData(data);
    g.drawImage(cv, 0, 0, W, H - 1, 0, 1, W, H - 1);
    for (let x = 0; x < W; x++) {
      const f = F0 + (F1 - F0) * x / W, v = data[Math.round(f / hz)] || 0, c = col(v), k = x * 4;
      row.data[k] = c[0]; row.data[k + 1] = c[1]; row.data[k + 2] = c[2]; row.data[k + 3] = 255;
    }
    g.putImageData(row, 0, 0);
    const mx = Math.round((freq - F0) / (F1 - F0) * W);
    g.fillStyle = state ? '#ffcf5a' : '#d5a63a'; g.fillRect(mx - 1, 0, 2, 1);
    const sv = $('rxSnr'); if (sv) sv.textContent = (snrDb > 0 ? Math.round(snrDb) : 0) + ' dB';
    const wv = $('rxWpm'); if (wv) wv.textContent = Math.round(1200 / ditMs) + ' WPM';
  };
  step();
}

/* ---------------- copy test ---------------- */
const copyTest = { on: false, got: '' };
function compare() {
  const mine = ($('rxMine').value || '').toUpperCase().replace(/\s+/g, ' ').trim();
  const dec = copyTest.got.toUpperCase().replace(/\*/g, '').replace(/\s+/g, ' ').trim();
  const out = $('rxCmp');
  if (!mine || !dec) { out.innerHTML = 'Start a copy test, copy what you hear, then press Compare.'; return; }
  const m2 = mine.replace(/ /g, ''), d2 = dec.replace(/ /g, '');   // don't count spacing differences
  const d = K().lev(m2, d2), pct = Math.max(0, Math.round((1 - d / Math.max(m2.length, d2.length)) * 100));
  out.innerHTML = `<b>${pct}% match</b> with the decoder.<br><span class="dim">Decoder heard:</span> <code>${dec.replace(/[<>&]/g, '')}</code><br><span class="dim">Remember: the decoder can be wrong too — weak or sloppy signals fool it.</span>`;
}

/* ---------------- ui ---------------- */
function msg(t) { const m = $('rxMsg'); if (m) m.textContent = t || ''; }
function ui(on) {
  const b = $('rxStop'); if (b) b.disabled = !on;
  const s = $('rxState'); if (s) s.textContent = on ? 'LISTENING' : 'STOPPED';
  const card = $('rxCard'); if (card) card.classList.toggle('live', on);
}
function init() {
  if (!$('rxWf')) return;
  if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) { const t = $('rxTab'); if (t) { t.disabled = true; t.title = 'Needs Chrome or Edge on a computer'; } const n = $('rxTabNote'); if (n) n.hidden = false; }
  $('rxMic').addEventListener('click', useMic);
  $('rxTab').addEventListener('click', useTab);
  $('rxTest').addEventListener('click', () => useTest());
  $('rxStop').addEventListener('click', stop);
  $('rxClear').addEventListener('click', () => { text = ''; emit(''); });
  const syncAuto = () => { const on = $('rxAuto').checked; auto = on; const l = $('rxAutoLbl'); if (l) l.textContent = 'AUTO-FIND: ' + (on ? 'ON' : 'OFF'); const m = $('rxManual'); if (m) m.hidden = on; const t = $('rxTone'); if (t) { t.value = Math.round(freq / 10) * 10; $('rxToneV').textContent = Math.round(freq) + ' Hz'; } };
  $('rxAuto').addEventListener('change', syncAuto);
  if ($('rxTone')) $('rxTone').addEventListener('input', e => { setFreq(+e.target.value); $('rxToneV').textContent = e.target.value + ' Hz'; resetDecoder(); });
  $('rxWf').addEventListener('click', e => {
    const r = e.target.getBoundingClientRect(), f = F0 + (F1 - F0) * (e.clientX - r.left) / r.width;
    setFreq(f); $('rxAuto').checked = false; syncAuto(); resetDecoder();
  });
  $('rxCopyGo').addEventListener('click', () => { copyTest.on = true; copyTest.got = ''; $('rxMine').value = ''; $('rxMine').focus(); $('rxCmp').innerHTML = 'Copying… type what you hear, then press Compare.'; });
  $('rxCopyCmp').addEventListener('click', () => { compare(); copyTest.on = false; });
  setFreq(freq);
  document.addEventListener('kpccw:mode', e => { if (e.detail !== 'listen') stop(); });
}
window.KPCRX = { get marks() { return marks.slice(); }, useTest, stop, setFreq, get text() { return text; }, get freq() { return freq; }, get wpm() { return 1200 / ditMs; }, get running() { return running; } };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
