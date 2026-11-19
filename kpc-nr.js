/* KPC app: 🎚 LISTENING CLEAN-UP — noise reduction, noise blanker, auto-notch and a filter for what you HEAR through the app
   (Nov 6 2026, Opus; the SDR handoff, section 6; Brandon: 'do next session').

   ONLY THE LISTENING PATHS: 🔊 HEAR THE RADIO HERE (kpc-native.js monitor) and the sound the PC sends to a phone on the REMOTE link
   (sendStream). NEVER the decoders: FT8 / FT4 / RTTY / PSK / SSTV / the AUDIO scope all read the raw capture, before any of this
   (the handoff: 'NR can erase digital signals; the digital path bypasses it'). Nothing here touches what goes to the radio.

   The chain:  radio sound → FILTER (Web Audio biquads, 3 high-pass + 3 low-pass) → kpc-nr worklet: NOISE BLANKER → AUTO-NOTCH →
               NOISE REDUCTION → speakers / phone.   One switch each; A/B = hear it with everything off, same loudness path.
     FILTER   off · voice 250–2800 Hz · CW pitch ± 250 Hz (pitch 500 / 600 / 700 / 800) · wide 100–3500 Hz
     CW PEAK  (Nov 11) with FILTER CW: a peaking biquad on the pitch, Q 12, +12 dB
     BLANKER  impulses (ignition, electric fence) far above the running level are muted for 1.5 ms with short ramps
     NOTCH    adaptive line enhancer (normalised LMS, 48 taps, 32-sample delay): a steady carrier is predictable, speech is not,
              so the predictable part is taken away. OFF for CW (it would notch the CW you want).
     NR       short-time spectrum (512-point FFT, half overlap, √Hann), the noise floor tracked per bin (follows it down at once,
              up slowly), Wiener gain with decision-directed SNR, a floor so it never goes silent (light −9 dB, medium −14,
              strong −20), gains smoothed across neighbouring bins against 'musical' warble. ≈ 10.7 ms delay at 48 kHz (511 samples).
   The DSP core (NRCore) is plain JS: the worklet runs it on the audio thread, the tests run it on recorded-style test sound.
   Settings: localStorage kpcAppNr. */
(function (G) {
  'use strict';
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const S = Object.assign({ nr: 'off', nb: false, notch: false, filt: 'off', bypass: false, pitch: 600, apf: false, cww: 500 }, LS('kpcAppNr', {}), { bypass: false });
  /* Nov 18 (NR review 3.7): A/B is a moment-to-moment comparison: B (all off) is never saved, so the app never opens in B */
  const save = () => SV('kpcAppNr', Object.assign({}, S, { bypass: false }));
  
  /* ======================================================================== the DSP core (also the worklet's body) */
  function NRCore(sr) {
    /* Nov 18 (NR review: sample rates, CW): the frame size follows the sample rate (512 at 44.1 / 48 kHz, 1024 at 88.2 / 96 kHz: the
       same ~94 Hz slices) and FILTER CW asks for 4× longer frames (~23 Hz slices: a weak CW note stands out of the hiss; more delay,
       which is fine for CW). set({ n }) changes it (the noise is learnt again). */
    const SRX = sr >= 88000 ? 2 : 1;
    let N = 0, H = 0, B = 0, BITS = 0, win, rev, re, im, inBuf, outAcc, RB = 0, ring, noise, ps, gPrev, pPrev, g, gs;
    let inN = 0, rw = 0, rr = 0, rc = 0, frames = 0;
    function size(n) {
      N = n; H = N / 2; B = N / 2 + 1; BITS = Math.round(Math.log2(N));
      win = new Float32Array(N); for (let i = 0; i < N; i++) win[i] = Math.sqrt(0.5 - 0.5 * Math.cos(2 * Math.PI * i / N));
      rev = new Uint16Array(N); for (let i = 0; i < N; i++) { let r = 0; for (let k = 0; k < BITS; k++) if (i & (1 << k)) r |= 1 << (BITS - 1 - k); rev[i] = r; }
      re = new Float32Array(N); im = new Float32Array(N); inBuf = new Float32Array(N); outAcc = new Float32Array(N); RB = 4 * N; ring = new Float32Array(RB);
      noise = new Float32Array(B).fill(1e-6); ps = new Float32Array(B); gPrev = new Float32Array(B).fill(1); pPrev = new Float32Array(B); g = new Float32Array(B); gs = new Float32Array(B);
      inN = 0; rw = 0; rr = 0; rc = 0; frames = 0;
    }
    size(512 * SRX);
    function fft(inv) {
      for (let i = 0; i < N; i++) { const j = rev[i]; if (j > i) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
      for (let len = 2; len <= N; len <<= 1) { const a = (inv ? 2 : -2) * Math.PI / len, wr = Math.cos(a), wi = Math.sin(a), h = len >> 1;
        for (let i = 0; i < N; i += len) { let cr = 1, ci = 0; for (let k = 0; k < h; k++) { const ar = re[i + k], ai = im[i + k], br = re[i + k + h], bi = im[i + k + h], vr = br * cr - bi * ci, vi = br * ci + bi * cr;
          re[i + k] = ar + vr; im[i + k] = ai + vi; re[i + k + h] = ar - vr; im[i + k + h] = ai - vi; const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr; } } }
      if (inv) for (let i = 0; i < N; i++) { re[i] /= N; im[i] /= N; }
    }
    /* blanker */
    let env = 1e-3, blank = 0, bGain = 1, lp = 0, seen = 0, shut = 0, fast = 0; const SHUT = Math.round(0.003 * sr), QUIET = 1e-5; const bLen = Math.round(0.0015 * sr), bRamp = Math.max(4, Math.round(0.0003 * sr)), LA = bRamp + 4, look = new Float32Array(LA);   /* look-ahead: the gate is shut before the click gets through */
    /* notch (adaptive line enhancer) */
    const L = Math.round(48 * sr / 48000), D = Math.round(32 * sr / 48000), w = new Float32Array(L), hist = new Float32Array(L + D + 1); let hp = 0, pow = 1e-4;   /* Nov 18: the same 1 ms memory at any rate */
    const o = { nr: 'off', nb: false, notch: false, bypass: false, floor: 1, over: 1, stage: '', n: 512 };
    let quietF = 0, skipF = 0;   /* NR: frames of dead silence in a row; frames to let pass when sound comes back */
    const self = {
      set(p) {
        /* Nov 18 (NR review 3.2): NR learns the noise again whenever it is switched on (or B goes back to A), not only at start-up */
        const was = o.nr !== 'off' && !o.bypass; Object.assign(o, p || {}); if (!was && o.nr !== 'off' && !o.bypass) frames = 0;
        if (p && p.n && p.n * SRX !== N) size(Math.max(256, Math.min(4096, p.n)) * SRX); o.floor = { off: 1, light: 0.35, medium: 0.2, strong: 0.1 }[o.nr] || 1; o.over = { off: 1, light: 1, medium: 1.4, strong: 2 }[o.nr] || 1; },
      get latency() { return o.stage === 'nb' ? 0 : N - 1; },   /* Nov 18 (NR review 3.8): 511 samples ≈ 10.7 ms at 48 kHz (it was really 768 = 16 ms) */
      process(x, y) {               /* x in, y out (same length; y may be x) */
        for (let n = 0; n < x.length; n++) {
          let v = x[n]; if (!(v > -10 && v < 10)) v = 0;   /* Nov 18 (NR review 3.9): one NaN / Infinity sample used to silence the sound for good */
          if (!o.bypass) {
            if (o.nb) {
              const a = Math.abs(v), late = look[lp]; look[lp] = v; lp = (lp + 1) % LA;
              /* Nov 18 (NR review 3.1): it used to lock shut for good after a quiet gap (the level learnt ≈ 0, everything after looked
                 like a click, and it never learnt while shut), and it muted strong CW. Now: dead silence teaches nothing; it keeps
                 learning slowly while shut; and the gate never stays shut more than 3 ms in a row (a real click is 1–2 ms):
                 past that it opens and learns the new level fast. */
              if (a >= QUIET) {
                if (seen < 0.1 * sr || fast > 0) { seen++; if (fast > 0) fast--; env = env * 0.99 + a * 0.01; }               /* the first 0.1 s (of sound) / after a long 'click': learn fast */
                else if (a > 8 * env + 0.02 && shut < SHUT) blank = bLen + LA;                   /* seen now, shut the gate on the delayed sound */
                else if (blank <= 0) env = env * 0.999 + a * 0.001;
                else env = env * 0.9999 + a * 0.0001;                                            /* shut: still learning, slowly */
              }
              if (blank > 0) { blank--; shut++; bGain = Math.max(0, bGain - 1 / bRamp);
                if (shut >= SHUT) { blank = 0; fast = Math.round(0.02 * sr); env = Math.max(env, a / 4); } }   /* too long for a click: open, relearn */
              else { if (bGain >= 1) shut = 0; bGain = Math.min(1, bGain + 1 / bRamp); }
              v = late * bGain;
            }
            if (o.notch) {
              hist[hp] = v; let yv = 0; const base = hp - D;
              for (let k = 0; k < L; k++) { const idx = (base - k + hist.length * 2) % hist.length; yv += w[k] * hist[idx]; }
              pow = pow * 0.995 + v * v * 0.005;
              const e = v - yv, mu = 0.004 / (pow * L + 1e-6);
              for (let k = 0; k < L; k++) { const idx = (base - k + hist.length * 2) % hist.length; w[k] = w[k] * 0.99995 + mu * e * hist[idx]; }
              hp = (hp + 1) % hist.length; v = e;
              if (!(v > -10 && v < 10)) { w.fill(0); hist.fill(0); pow = 1e-4; v = 0; }   /* never let a bad number live in the notch */
            }
          }
          if (o.stage === 'nb') { y[n] = v; continue; }   /* Nov 18: the blanker-only stage in front of the filter: no frames, no delay */
          /* NR on a block basis: every H samples one frame; the output is delayed N samples (also in bypass, so A/B stays in time) */
          inBuf[inN++] = v;
          if (inN === N) {
            frames++;
            for (let i = 0; i < N; i++) { re[i] = inBuf[i] * win[i]; im[i] = 0; }
            if (o.nr !== 'off' && !o.bypass) {
              fft(false);
              /* Nov 18 (NR review 3.2): dead silence (radio muted while transmitting, start-up) teaches nothing, and when sound comes
                 back after it the floor is learnt again fast; the floor never drops below a tiny minimum (from 0, ×1.003 never climbs) */
              let E = 0; for (let k = 0; k < B; k++) E += re[k] * re[k] + im[k] * im[k];
              const dead = E < 1e-9;
              if (dead) { quietF++; frames = Math.min(frames, 1); } else { if (quietF > 8) skipF = 2; quietF = 0; }
              const skip = !dead && skipF > 0; if (skip) { skipF--; frames = 0; }   /* the 2 frames where sound comes back are half silence: learn after them */
              for (let k = 0; k < B; k++) {
                const P = re[k] * re[k] + im[k] * im[k];
                if (dead || skip) { g[k] = 1; continue; }
                ps[k] = frames < 3 ? P : ps[k] * 0.7 + P * 0.3;
                if (frames < 20) noise[k] = frames === 1 ? ps[k] : Math.min(noise[k] * 1.05, ps[k] + noise[k] * 0.5);   /* start: learn the floor fast */
                else if (ps[k] < noise[k]) noise[k] = noise[k] * 0.8 + ps[k] * 0.2; else noise[k] *= 1.003;              /* down at once, up ~3 dB a second */
                if (noise[k] < 1e-12) noise[k] = 1e-12;
                const nk = noise[k] * o.over + 1e-12, post = P / nk, prio = 0.98 * (gPrev[k] * gPrev[k] * pPrev[k]) / nk + 0.02 * Math.max(post - 1, 0);
                g[k] = Math.max(o.floor, prio / (1 + prio)); pPrev[k] = P;
              }
              for (let k = 0; k < B; k++) gs[k] = (g[Math.max(0, k - 1)] + 2 * g[k] + g[Math.min(B - 1, k + 1)]) / 4;
              for (let k = 0; k < B; k++) { gPrev[k] = gs[k]; re[k] *= gs[k]; im[k] *= gs[k]; if (k > 0 && k < N / 2) { re[N - k] = re[k]; im[N - k] = -im[k]; } }
              fft(true);
            }
            for (let i = 0; i < N; i++) outAcc[i] += re[i] * win[i];
            for (let i = 0; i < H; i++) { ring[rw] = outAcc[i]; rw = (rw + 1) % RB; rc++; }
            outAcc.copyWithin(0, H); outAcc.fill(0, N - H);
            inBuf.copyWithin(0, H); inN = N - H;
          }
          if (rc > 0) { y[n] = ring[rr]; rr = (rr + 1) % RB; rc--; } else y[n] = 0;
        }
        return y;
      }
    };
    return self;
  }

  /* the worklet: NRCore on the audio thread, settings by message */
  const WORKLET = `${NRCore.toString()}
class KpcNr extends AudioWorkletProcessor {
  constructor(o) { super(); this.core = NRCore(sampleRate); this.core.set((o && o.processorOptions) || {}); this.port.onmessage = e => { if (e.data && e.data.stop) this.dead = true; else this.core.set(e.data); }; }
  process(inputs, outputs) { if (this.dead) return false; const i = inputs[0] && inputs[0][0], o = outputs[0] && outputs[0][0]; if (!o) return true; if (!i) { o.fill(0); return true; } this.core.process(i, o); for (let c = 1; c < outputs[0].length; c++) outputs[0][c].set(o); return true; }
}
registerProcessor('kpc-nr', KpcNr);`;
  let URLW = null; const READY = new WeakSet(), LIVE = new Set();
  async function prepare(ctx) {
    if (!ctx || !ctx.audioWorklet || READY.has(ctx)) return READY.has(ctx);
    try { if (!URLW) URLW = URL.createObjectURL(new Blob([WORKLET], { type: 'application/javascript' })); await ctx.audioWorklet.addModule(URLW); READY.add(ctx); return true; } catch (e) { return false; }
  }
  const FILT = { off: [20, 20000], voice: [250, 2800], cw: [null, null], wide: [100, 3500] };
  function edges() { if (S.filt === 'cw') { const p = +S.pitch || 600, w = +S.cww || 500, h = w >= 500 ? w / 2 : w; return [Math.max(100, p - h), p + h]; } return FILT[S.filt] || FILT.off; }
  /* Nov 18: CW 500 / 250 / 100 Hz. 500 = the old ±250 Hz skirts. 250 and 100 = three band-pass stages on the pitch (Q set so the
     three together are that wide at −3 dB) inside skirts twice as wide: the pitch stays at full level, a signal 200 Hz away from a
     100 Hz filter is down ~25 dB. Off = the stages are flat (peaking, 0 dB). */
  const narrowQ = () => (S.filt === 'cw' && !S.bypass && (+S.cww || 500) < 500) ? (+S.pitch || 600) / ((+S.cww || 500) * 1.96) : 0;
  const peakDb = () => (S.apf && S.filt === 'cw' && !S.bypass ? 12 : 0);
  /* Nov 18 (NR review 3.4): the BLANKER runs in its own small stage IN FRONT of the filter (a filter smears a click into a soft
     'bonk' the blanker cannot see); the main stage after the filter does notch + NR. FILTER CW = 4× longer NR frames. */
  function params() { return { nr: S.nr, nb: false, notch: !!S.notch && S.filt !== 'cw', bypass: !!S.bypass, n: S.filt === 'cw' ? 2048 : 512 }; }
  function nbParams() { return { stage: 'nb', nb: !!S.nb, notch: false, nr: 'off', bypass: !!S.bypass }; }
  /* a chain in this AudioContext: {input, output}. With the worklet when the module is loaded (prepare), else the filter alone. */
  function chain(ctx) {
    /* Nov 18 (NR review 3.3): a real 6th-order Butterworth needs three DIFFERENT Q values (0.518 / 0.707 / 1.932). Three times
       0.707 (read by Web Audio as 0.707 dB) bent the band edges. Review 3.7: a chain built while B is on starts open. */
    /* Web Audio's highpass / lowpass Q is in dB (10^(Q/20) = the textbook Q): 0.5176 / 0.7071 / 1.9319 → −5.72 / −3.01 / +5.72 dB */
    const QS = [-5.7199, -3.0103, 5.7199];
    const mk = (type, f, i) => { const b = ctx.createBiquadFilter(); b.type = type; b.frequency.value = f; b.Q.value = QS[i % 3]; return b; };
    const [lo, hi] = S.bypass ? [20, 20000] : edges(), bq = [mk('highpass', lo, 0), mk('highpass', lo, 1), mk('highpass', lo, 2), mk('lowpass', hi, 0), mk('lowpass', hi, 1), mk('lowpass', hi, 2)];   /* 3 + 3 stages: 36 dB an octave */
    for (let i = 0; i < bq.length - 1; i++) bq[i].connect(bq[i + 1]);
    /* Nov 11 (Brandon: 'any improvement to digital filters'): CW PEAK = a narrow +12 dB boost right on the CW pitch (an audio peak
       filter, like the radio's APF): the one signal you are copying stands out of the others inside the CW filter. Only with FILTER CW. */
    const nq = narrowQ(), bp = [0, 1, 2].map(() => { const b = ctx.createBiquadFilter(); b.type = nq ? 'bandpass' : 'peaking'; b.frequency.value = +S.pitch || 600; b.Q.value = nq || 1; b.gain.value = 0; return b; });
    bq[bq.length - 1].connect(bp[0]); bp[0].connect(bp[1]); bp[1].connect(bp[2]);
    const pk = ctx.createBiquadFilter(); pk.type = 'peaking'; pk.frequency.value = +S.pitch || 600; pk.Q.value = 12; pk.gain.value = peakDb(); bp[2].connect(pk);
    /* Nov 18 (NR review 3.6): headroom for CW PEAK: everything goes down by the peak's lift, so the pitch stays at its old level
       (no clipping on a strong signal) and the rest drops 12 dB, like a radio's APF */
    const hd = ctx.createGain(); hd.gain.value = Math.pow(10, -peakDb() / 20); pk.connect(hd);
    let out = hd, node = null, nbn = null, input = bq[0];
    if (READY.has(ctx)) {
      try { node = new AudioWorkletNode(ctx, 'kpc-nr', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1], channelCount: 1, channelCountMode: 'explicit', processorOptions: params() }); hd.connect(node); out = node; } catch (e) { node = null; }
      try { nbn = new AudioWorkletNode(ctx, 'kpc-nr', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1], channelCount: 1, channelCountMode: 'explicit', processorOptions: nbParams() }); nbn.connect(bq[0]); input = nbn; } catch (e) { nbn = null; }
    }
    /* Nov 18 (NR review 3.5 + 'fades'): A/B at the SAME loudness: two level meters (before / after the clean-up) learn how much
       quieter A makes the sound, and B is turned down by that much; every switch fades out and back in over ~25 ms (no pops). */
    const ab = ctx.createGain(); ab.gain.value = 1; out.connect(ab);
    let anIn = null, anOut = null; try { anIn = ctx.createAnalyser(); anIn.fftSize = 2048; anOut = ctx.createAnalyser(); anOut.fftSize = 2048; input.connect(anIn); out.connect(anOut); } catch (e) {}
    const c = { ctx, input, output: ab, node, nbn, bq, bp, pk, hd, ab, anIn, anOut, ratio: 1 };
    c.release = () => { LIVE.delete(c); try { [nbn, ...bq, ...bp, pk, hd, node, ab, anIn, anOut].forEach(x => { if (x) x.disconnect(); }); } catch (e) {} [node, nbn].forEach(x => { if (x) try { x.port.postMessage({ stop: 1 }); } catch (e) {} }); };   /* review 3.10 */
    LIVE.add(c); return c;
  }
  const rmsOf = an => { if (!an) return 0; const b = new Float32Array(an.fftSize); an.getFloatTimeDomainData(b); let s = 0; for (let i = 0; i < b.length; i++) s += b[i] * b[i]; return Math.sqrt(s / b.length); };
  function abLevel() {
    for (const c of LIVE) {
      if (c.ctx.state === 'closed') { LIVE.delete(c); continue; }
      const i = rmsOf(c.anIn), o = rmsOf(c.anOut);
      if (!S.bypass && i > 1e-4 && o > 0) c.ratio = c.ratio * 0.8 + Math.max(0.05, Math.min(4, o / i)) * 0.2;   /* how A changes the loudness, learnt while on A */
      if (!c.fading) c.ab.gain.setTargetAtTime(S.bypass ? c.ratio : 1, c.ctx.currentTime, 0.05);
    }
  }
  setInterval(abLevel, 250);
  function apply() {
    const [lo, hi] = S.bypass ? [20, 20000] : edges();
    for (const c of LIVE) {
      if (c.ctx.state === 'closed') { LIVE.delete(c); continue; }
      const t = c.ctx.currentTime; c.bq.forEach((b, i) => b.frequency.setTargetAtTime(i < 3 ? lo : hi, t, 0.02));
      if (c.pk) { c.pk.frequency.setTargetAtTime(+S.pitch || 600, t, 0.02); c.pk.gain.setTargetAtTime(peakDb(), t, 0.02); }
      if (c.hd) c.hd.gain.setTargetAtTime(Math.pow(10, -peakDb() / 20), t, 0.02);
      if (c.bp) { const nq = narrowQ(); c.bp.forEach(b => { b.type = nq ? 'bandpass' : 'peaking'; b.gain.value = 0; b.frequency.setTargetAtTime(+S.pitch || 600, t, 0.02); b.Q.setTargetAtTime(nq || 1, t, 0.02); }); }
      /* fade out, switch, fade back in (Nov 18: no pops when NR / notch / blanker / A-B switch) */
      const ab = c.ab.gain; c.fading = true; try { ab.cancelScheduledValues(t); ab.setTargetAtTime(0, t, 0.004); ab.setTargetAtTime(S.bypass ? c.ratio : 1, t + 0.02, 0.008); } catch (e) {}
      setTimeout(() => { if (c.node) c.node.port.postMessage(params()); if (c.nbn) c.nbn.port.postMessage(nbParams()); }, 14);
      setTimeout(() => { c.fading = false; }, 80);
    }
  }
  function set(p) { Object.assign(S, p || {}); save(); apply(); draw(); }
  const active = () => !S.bypass && (S.nr !== 'off' || S.nb || S.notch || S.filt !== 'off');

  /* ======================================================================== the controls: STATION → Sound (under 🔊 HEAR THE RADIO HERE) + the RADIO screen */
  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function html(id, ext) {
    const ch = (k, v, t) => `<button type="button" class="chip${S[k] === v ? ' on' : ''}" data-nrk="${k}" data-nrv="${esc(v)}">${t}</button>`;
    const tg = (k, t) => `<button type="button" class="chip${S[k] ? ' on' : ''}" data-nrt="${k}">${t}</button>`;
    return `<div class="nrbox" id="${id}"${ext ? ' data-nr-ext="1"' : ''}><div class="nrh">🎚 WHAT YOU HEAR HERE <small>${ext ? '(only what you hear; FT8 and the other decoders always get the untouched sound)' : '(speakers + the phone on the remote link; never the decoders)'}</small></div>
      <div class="nrrow"><span>NOISE REDUCTION</span>${ch('nr', 'off', 'OFF')}${ch('nr', 'light', 'LIGHT')}${ch('nr', 'medium', 'MEDIUM')}${ch('nr', 'strong', 'STRONG')}</div>
      <div class="nrrow"><span>FILTER</span>${ch('filt', 'off', 'OFF')}${ch('filt', 'voice', 'VOICE')}${ch('filt', 'cw', 'CW')}${ch('filt', 'wide', 'WIDE')}</div>
      <div class="nrrow"><span>MORE</span>${tg('nb', 'BLANKER')}${tg('notch', 'AUTO-NOTCH')}<button type="button" class="chip nrab${S.bypass ? ' on' : ''}" data-nrt="bypass">${S.bypass ? 'B: ALL OFF' : 'A/B'}</button></div>
      ${S.filt === 'cw' ? `<div class="nrrow"><span>CW PITCH</span>${[500, 600, 700, 800].map(v => `<button type="button" class="chip${(+S.pitch || 600) === v ? ' on' : ''}" data-nrp="${v}">${v}</button>`).join('')}${tg('apf', '🎯 PEAK')}</div>
      <div class="nrrow"><span>CW WIDTH</span>${[500, 250, 100].map(v => `<button type="button" class="chip${(+S.cww || 500) === v ? ' on' : ''}" data-nrw="${v}">${v} Hz</button>`).join('')}</div>` : ''}
      ${S.notch && S.filt === 'cw' ? '<p class="hint">Auto-notch is off with the CW filter: it would take the CW out.</p>' : ''}${S.nb ? '<p class="hint">The radio\'s own noise blanker works better when it has one: this one only gets what comes out of the radio\'s filter.</p>' : ''}</div>`;
  }
  function draw() {
    const lv = $('stLevels'); if (lv && !$('stNr')) lv.insertAdjacentHTML('afterend', html('stNr')); else if ($('stNr')) $('stNr').outerHTML = html('stNr');
    const rd = $('rdTalk'); if (rd && !$('rdNr')) rd.insertAdjacentHTML('beforebegin', html('rdNr')); else if ($('rdNr')) $('rdNr').outerHTML = html('rdNr');
    document.querySelectorAll('.nrbox[data-nr-ext]').forEach(b => { b.outerHTML = html(b.id, true); });   /* Nov 7: boxes other pages put in (the website's Hunters Lounge) */
  }
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-nrk],[data-nrt],[data-nrp],[data-nrw]'); if (!b) return;
    if (b.dataset.nrw) set({ cww: +b.dataset.nrw }); else if (b.dataset.nrp) set({ pitch: +b.dataset.nrp }); else if (b.dataset.nrk) set({ [b.dataset.nrk]: b.dataset.nrv }); else set({ [b.dataset.nrt]: !S[b.dataset.nrt] });
    const A = G.KPCApp, mon = A && A.S && A.S.mon;
    if (A && !mon && !(G.KPCRemote && KPCRemote.base && KPCRemote.clients && KPCRemote.clients().length) && !draw.said) { draw.said = true; A.toast('🎚 This changes what you hear through the app: turn on 🔊 HEAR THE RADIO HERE (STATION → Sound), or listen on the phone over the remote link.', 5000); }
  });
  let tries = 0; const boot = () => { if (!G.KPCApp) { if (++tries < 50) setTimeout(boot, 200); return; }   /* Nov 7: on a website page with no app, stop looking after 10 s */ draw(); KPCApp.on('screen', n => { if (n === 'station' || n === 'radio') setTimeout(draw, 60); }); };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();

  G.KPCNR = { S, set, prepare, chain, apply, active, params, nbParams, edges, NRCore, draw, html, abLevel, _live: () => LIVE.size, _chains: () => [...LIVE] };
})(window);
