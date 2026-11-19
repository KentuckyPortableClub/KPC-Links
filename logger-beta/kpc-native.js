/* KPC native bridge. On Android (inside the app) the radio sound and the USB radio go through the app's own code
   (plugins/kpc-native: KpcAudio + KpcSerial). On Windows (Electron) and in a browser the web ways are used instead
   (Web Audio with no call-mode processing; Web Serial). The page code only ever talks to window.KPCNative.
     KPCNative.native           true inside the Android app
     KPCNative.audio.devices()  -> {inputs:[{id,name,usb}], outputs:[...]}
     KPCNative.audio.start({input, output}, onRx)  onRx({pcm: Float32Array 12 kHz, t: ms of first sample, db, peak})
     KPCNative.audio.stop()
     KPCNative.audio.play(Float32Array 48 kHz, atMs, id) -> Promise resolved when it has gone out ({state:'end'|'stopped'})
     KPCNative.audio.tone(hz, seconds) -> Promise (same)
     KPCNative.audio.stopTx(), setGain(0..1)
     KPCNative.serial           Android only: ports() -> Web-Serial-like port objects for kpc-cat.js; letGo() drops the USB port (touch-and-go) */
(function (G) {
  /* window.Capacitor comes from capacitor.js (copied from @capacitor/core at build time, loaded before this file); inside the app it
     merges with the bridge Android injects. Oct 20: without capacitor.js the page had no registerPlugin and silently used the web path. */
  const C = G.Capacitor, NATIVE = !!(C && C.isNativePlatform && C.isNativePlatform() && C.registerPlugin);
  if (C && C.isNativePlatform && C.isNativePlatform() && !C.registerPlugin) console.error('KPCNative: Capacitor bridge without registerPlugin (capacitor.js missing?)');
  const KA = NATIVE ? C.registerPlugin('KpcAudio') : null, KS = NATIVE ? C.registerPlugin('KpcSerial') : null;
  const RATE = 48000, DEC = 4;

  function b64toBytes(s) { const bin = atob(s), out = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; }
  function bytesToB64(u8) { let s = ''; for (let i = 0; i < u8.length; i += 8192) s += String.fromCharCode.apply(null, u8.subarray(i, i + 8192)); return btoa(s); }
  function b64toF32(s) { const u8 = b64toBytes(s), i16 = new Int16Array(u8.buffer, u8.byteOffset, u8.length >> 1), f = new Float32Array(i16.length); for (let i = 0; i < i16.length; i++) f[i] = i16[i] / 32768; return f; }
  function f32toB64(f) { const i16 = new Int16Array(f.length); for (let i = 0; i < f.length; i++) { const v = Math.round(f[i] * 32767); i16[i] = v > 32767 ? 32767 : v < -32768 ? -32768 : v; } return bytesToB64(new Uint8Array(i16.buffer)); }

  /* ---------- sound ---------- */
  let onRx = null, rxH = null, txH = null, txWait = {};
  /* the voice chain (shaper → compressor → VOICE LEVEL → limiter → SSB band-limit → key-up delay → gate) from any source node to any output: pipe() uses it; tests run it in an OfflineAudioContext */
  function voiceChain(ctx, src, out, preset) {
    const gate = ctx.createGain(); gate.gain.value = 0;
    const hp = ctx.createBiquadFilter(), pk = ctx.createBiquadFilter(), lp = ctx.createBiquadFilter(), comp = ctx.createDynamicsCompressor(), mk = ctx.createGain();
    hp.type = 'highpass'; pk.type = 'peaking'; lp.type = 'lowpass';
    const vg = ctx.createGain(); vg.gain.value = 1;   /* Oct 27: MY VOICE LEVEL (the phone's own slider), apart from the FT8 TX LEVEL */
    /* Nov 18 full review (OP-W2): a LIMITER last in the chain (−3 dB ceiling, fast) so VOICE LEVEL up to +30 dB can't overdrive the radio's
       input (splatter), and a level reading AFTER it (txDb) for the 🎙 bar on RADIO */
    /* Nov 18 SSB review (1.2-B): the limiter is a CEILING only (−3 dB, 100 ms release: it touches only peaks over it; at +30 dB VOICE LEVEL a 20:1 ceiling at −1 dB went over full scale), the compressor does the work */
    const lim = ctx.createDynamicsCompressor(); lim.threshold.value = -3; lim.knee.value = 0; lim.ratio.value = 20; lim.attack.value = 0.002; lim.release.value = 0.1;
    const tan = ctx.createAnalyser(); tan.fftSize = 1024; const tbuf = new Float32Array(tan.fftSize);
    /* Nov 18 SSB review (1.2-A): a steep FIR band-limit after everything that can add highs (compressor, limiter): flat to 2.7 kHz,
       ≥ 40 dB down from 3.0 kHz (a 1023-tap Blackman windowed sinc, linear phase, ~10 ms). One biquad at 3-6 kHz left the voice wide. */
    /* the browser's compressor adds its own make-up gain (~+1.7 dB at these settings): taken back off, then a soft clip that only a
       peak still over −1 dBFS ever reaches (its harmonics land above 3 kHz, where the band-limit right after removes them) */
    const lpg = ctx.createGain(); lpg.gain.value = Math.pow(10, -1.8 / 20);
    const clip = ctx.createWaveShaper(); clip.curve = softClip(); clip.oversample = '2x';
    const fir = ctx.createConvolver(); fir.normalize = false; fir.buffer = ssbFir(ctx);
    /* Nov 18 SSB review (1.2-D): a delay line so speech from the moment of the press is not lost while the radio keys (set by delay()) */
    const dl = ctx.createDelay(1.0); dl.delayTime.value = 0;
    src.connect(hp); hp.connect(pk); pk.connect(lp); lp.connect(comp); comp.connect(mk); mk.connect(vg); vg.connect(lim); lim.connect(lpg); lpg.connect(clip); clip.connect(fir); fir.connect(dl); dl.connect(gate); dl.connect(tan); gate.connect(out);
    /* Nov 1: a level reading of the phone's voice as it reaches the PC (before the gate), for the builders' report */
    const an = ctx.createAnalyser(); an.fftSize = 1024; src.connect(an); const abuf = new Float32Array(an.fftSize);
    /* Nov 18 SSB review (1.2-A/C): natural = 120 Hz up with mild speech processing (−14 dB, 2.5:1), so its talk power is useful too */
    const P = { natural: { hp: 120, pkHz: 2500, pkDb: 0, lp: 3200, th: -14, ratio: 2.5, mk: 1.25 }, punch: { hp: 250, pkHz: 2500, pkDb: 4, lp: 3200, th: -20, ratio: 4, mk: 1.3 }, contest: { hp: 350, pkHz: 2600, pkDb: 7, lp: 3000, th: -28, ratio: 10, mk: 1.7 } };
    const shape = name => { const q = P[name] || P.natural; hp.frequency.value = q.hp; pk.frequency.value = q.pkHz; pk.Q.value = 1.1; pk.gain.value = q.pkDb; lp.frequency.value = q.lp; comp.threshold.value = q.th; comp.ratio.value = q.ratio; comp.attack.value = 0.003; comp.release.value = 0.12; comp.knee.value = 6; mk.gain.value = q.mk; return name in P ? name : 'natural'; };
    shape(preset || 'natural');
    return { _gate: gate, delay: sec => { dl.delayTime.value = Math.max(0, Math.min(0.95, +sec || 0)); }   /* Nov 18 review: up to 0.95 s (a slow DATA switch) */, delayed: () => dl.delayTime.value, txDb: () => { tan.getFloatTimeDomainData(tbuf); let m = 0; for (let i = 0; i < tbuf.length; i++) m = Math.max(m, Math.abs(tbuf[i])); return { db: m > 0 ? Math.round(20 * Math.log10(m)) : -99, lim: Math.round(lim.reduction || 0) }; }, db: () => { an.getFloatTimeDomainData(abuf); let m = 0; for (let i = 0; i < abuf.length; i++) m = Math.max(m, Math.abs(abuf[i])); return m > 0 ? Math.round(20 * Math.log10(m)) : -99; }, gate: on => { gate.gain.value = on ? 1 : 0; }, level: db => { vg.gain.value = Math.pow(10, Math.max(-20, Math.min(30, +db || 0)) / 20); }, shape, stop: () => { try { src.disconnect(); gate.disconnect(); an.disconnect(); lim.disconnect(); lpg.disconnect(); clip.disconnect(); fir.disconnect(); dl.disconnect(); } catch (e) {} } };
  }
  let CLIP = null;
  function softClip() { if (CLIP) return CLIP; const n = 2049, c = new Float32Array(n), k = 0.85; for (let i = 0; i < n; i++) { const x = i / (n - 1) * 2 - 1, a = Math.abs(x); c[i] = a <= k ? x : Math.sign(x) * (k + (0.98 - k) * Math.tanh((a - k) / (0.98 - k))); } CLIP = c; return c; }
  /* the SSB band-limit: 1023-tap Blackman windowed-sinc low-pass, cut-off 2.85 kHz (made once per sample rate) */
  const FIRS = {};
  function ssbFir(ctx) {
    const r = ctx.sampleRate; if (FIRS[r] && FIRS[r].ctx === ctx) return FIRS[r].b;
    const N = 1023, fc = 2850 / r, b = ctx.createBuffer(1, N, r), h = b.getChannelData(0); let sum = 0;
    for (let i = 0; i < N; i++) { const m = i - (N - 1) / 2, x = m === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * m) / (Math.PI * m), w = 0.42 - 0.5 * Math.cos(2 * Math.PI * i / (N - 1)) + 0.08 * Math.cos(4 * Math.PI * i / (N - 1)); h[i] = x * w; sum += h[i]; }
    for (let i = 0; i < N; i++) h[i] /= sum;
    FIRS[r] = { ctx, b }; return b;
  }
  const audio = {
    rate: RATE,
    native: NATIVE,
    async devices() {
      if (NATIVE) return KA.devices();
      const out = { inputs: [], outputs: [] };
      try {
        if (!navigator.mediaDevices) return out;
        const ds = await navigator.mediaDevices.enumerateDevices();
        ds.forEach(d => { const o = { id: d.deviceId, name: d.label || (d.kind === 'audioinput' ? 'Microphone' : 'Speaker'), usb: /usb|codec|digirig|signalink|ic-|ft-|yaesu|icom/i.test(d.label || '') && !/^(default|communications)$/.test(d.deviceId), grp: d.groupId || '', sys: /^(default|communications)$/.test(d.deviceId) }; if (d.kind === 'audioinput') out.inputs.push(o); if (d.kind === 'audiooutput') out.outputs.push(o); });
      } catch (e) {}
      return out;
    },
    async start(o, cb) {
      o = o || {}; onRx = cb;
      if (NATIVE) {
        if (rxH) { try { rxH.remove(); } catch (e) {} }
        rxH = await KA.addListener('rx', ev => { if (!onRx) return; try { onRx({ pcm: b64toF32(ev.pcm), t: +ev.t, db: +ev.db, peak: +ev.peak, tx: !!ev.tx }); } catch (e) {} });
        if (!txH) txH = await KA.addListener('tx', ev => { const w = txWait[ev.id]; if (ev.state !== 'start' && w) { delete txWait[ev.id]; w(ev); } audio.txing = ev.state === 'start'; if (audio.onTx) audio.onTx(ev); });
        return KA.start({ input: o.input != null && o.input !== '' ? +o.input : -1, output: o.output != null && o.output !== '' ? +o.output : -1, maxVolume: o.maxVolume !== false, stereo: !!o.stereo, lowLatency: !!o.lowLatency, deep: !!o.deep, bufferMs: o.bufferMs || (o.deep ? 1000 : 250) });
      }
      return webStart(o);
    },
    async stop() { onRx = null; if (NATIVE) { try { if (rxH) rxH.remove(); } catch (e) {} rxH = null; try { return await KA.stop(); } finally { settleTx(0); } } return webStop(); },
    play(pcm48, atMs, id) {
      id = id || ('p' + Date.now().toString(36));
      if (NATIVE) return new Promise((res, rej) => { txWait[id] = res; KA.play({ pcm: f32toB64(pcm48), rate: RATE, at: atMs || 0, id, pauseRx: !!audio.pauseRx }).catch(e => { delete txWait[id]; rej(e); }); });
      return webPlay(pcm48, atMs, id);
    },
    tone(hz, seconds, id) {
      id = id || 'tone';
      if (NATIVE) return new Promise((res, rej) => { txWait[id] = res; KA.tone({ hz: hz || 1500, seconds: seconds || 10, id, pauseRx: !!audio.pauseRx }).catch(e => { delete txWait[id]; rej(e); }); });
      const n = Math.round((seconds || 10) * RATE), f = new Float32Array(n), r = RATE / 200;
      for (let i = 0; i < n; i++) f[i] = Math.sin(2 * Math.PI * (hz || 1500) * i / RATE) * Math.min(1, i / r, (n - 1 - i) / r);
      return webPlay(f, 0, id);
    },
    stopTx() { if (NATIVE) { settleTx(400); return KA.stopTx(); } return webStopTx(); },
    /* tone with nothing listening at all (Android only): closes the normal sound first; press START again afterwards */
    mediaTone(o) { o = o || {}; if (!NATIVE) return Promise.reject(new Error('Android only')); return KA.mediaTone({ hz: o.hz || 1500, seconds: o.seconds || 10 }); },
    toneOnly(o) { o = o || {}; if (!NATIVE) return Promise.reject(new Error('Android only')); onRx = null; return KA.toneOnly({ hz: o.hz || 1500, seconds: o.seconds || 10, stereo: o.stereo !== false, output: o.output != null && o.output !== '' ? +o.output : -1 }); },
    setGain(g) { audio.gain = Math.max(0, Math.min(1, +g || 0)); if (NATIVE) return KA.setGain({ gain: audio.gain }); if (wG) wG.gain.value = audio.gain; return Promise.resolve(); },
    status() { if (NATIVE) return KA.status(); return Promise.resolve({ running: !!wCtx, txing: !!wSrc, gain: audio.gain, capture: stat.how, blocks: stat.blocks, gaps: stat.gaps, anchors: stat.anchors, ctx: wCtx ? wCtx.state : '' }); },
    capture: () => Object.assign({}, stat),
    /* the remote link (Windows base station): the radio's sound as a stream the PC can send to the phone,
       and a way to play the phone's voice into the radio (through the TX LEVEL gain, with a gate the PTT opens) */
    rxStream() { return wStream || null; },
    /* 🔊 HEAR THE RADIO HERE (Oct 27, Fable): the radio's RX audio on this computer's speakers — its own AudioContext on a sink that is
       NOT the radio's sound card (setSinkId), gain in dB; rebuilt when the sound session changes; off while transmitting (pauseRx) */
    async monitor(on, sinkId, db) {
      try { if (mon.ctx) { try { mon.ctx.close(); } catch (e) {} mon.ctx = null; } if (!on) return { ok: true };
        if (!wCtx || !wStream) return { err: 'the sound is not running (press START)' };
        const AC = G.AudioContext || G.webkitAudioContext, c = new AC(); let where = 'this computer\'s speakers';
        if (c.setSinkId) { let id = sinkId || ''; if (!id) { try { const ds = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'audiooutput' && d.deviceId && d.deviceId !== 'communications' && d.deviceId !== audio.outDevId && !/usb audio codec|usb audio device|ft-|ic-|ts-|yaesu|icom|kenwood|digirig|signalink|codec/i.test(d.label || '')); const pick = ds.find(d => d.deviceId !== 'default') || ds[0]; if (pick) { id = pick.deviceId; where = pick.label || where; } } catch (e) {} }
          if (id) { try { await c.setSinkId(id); } catch (e) { where = 'Windows default output'; } } }
        if (c.state === 'suspended') await c.resume();
        const src = c.createMediaStreamSource(wStream), g = c.createGain(); g.gain.value = Math.pow(10, (+db || 0) / 20);
        /* Nov 6: 🎚 listening clean-up (kpc-nr.js: filter, blanker, notch, NR) between the radio and the speakers — never on the decoders' path */
        /* Nov 11: 🗣 DIGITAL VOICE on (kpc-dv.js) = the FreeDV decoder's speech instead (the raw radio sound when not in sync) */
        const dv = G.KPCDV && KPCDV.on() ? await KPCDV.rxChain(c, src) : null;
        if (dv) dv.output.connect(g);
        else if (G.KPCNR) { await KPCNR.prepare(c); const ch = KPCNR.chain(c); src.connect(ch.input); ch.output.connect(g); } else src.connect(g);
        g.connect(c.destination);
        mon = { ctx: c, g, gen: stat.gen }; return { ok: true, where };
      } catch (e) { return { err: e.message || String(e) }; }
    },
    monitorGain(db) { if (mon.g) mon.g.gain.value = Math.pow(10, (+db || 0) / 20); },
    /* Oct 26 (Fable; Brandon: 'volume wide open … need more volume' on the phone): what the PC SENDS the phone is a levelled copy of the
       radio's USB audio (gain + a compressor with make-up), since radio sound cards sit 20 dB down; built once per sound session */
    sendStream() {
      if (!wCtx || !wStream) return null;
      if (wSend && wSend.gen === stat.gen) return wSend.st;
      try { const src = wCtx.createMediaStreamSource(wStream), g = wCtx.createGain(), c = wCtx.createDynamicsCompressor(), mk = wCtx.createGain(), d = wCtx.createMediaStreamDestination(), nr = G.KPCNR ? KPCNR.chain(wCtx) : null;   /* Nov 6: the phone hears the cleaned-up sound too */
        g.gain.value = 4; c.threshold.value = -20; c.knee.value = 6; c.ratio.value = 8; c.attack.value = 0.005; c.release.value = 0.25; mk.gain.value = 1.6;
        if (nr) { src.connect(nr.input); nr.output.connect(g); } else src.connect(g); g.connect(c); c.connect(mk); mk.connect(d); wSend = { gen: stat.gen, st: d.stream, nodes: [src, g, c, mk, d] }; return d.stream; } catch (e) { return null; }
    },
    /* the phone's voice → the radio, through a VOICE SHAPER (Brandon Oct 22: 'contest microphones are higher pitched to break pile ups'):
       natural = straight through · punch = a little high-pass + presence · contest = tight high-pass, strong presence, hard compression (cuts through a pile-up) */
    pipe(stream, preset, o) {
      if (!wCtx) return null;
      /* Nov 11: 🗣 DIGITAL VOICE (kpc-dv.js; only kpc-radio's HOLD TO TALK asks, with o.dv when DV is on): mic → FreeDV modem → TX LEVEL, no voice shaper */
      if (o && o.dv) return G.KPCDV ? KPCDV.txPipe(wCtx, wCtx.createMediaStreamSource(stream), wG) : null;
      const ch = voiceChain(wCtx, wCtx.createMediaStreamSource(stream), wG, preset);
      /* Nov 18 review: 🎧 HEAR MY PROCESSED VOICE — what actually goes to the radio (after the shaper, limiter and band-limit, only while the
         gate is open) also plays on the HEAR THE RADIO HERE output. Needs that monitor on (it is the PC-speaker output). */
      if (audio.voiceMon && mon.ctx && ch && ch._gate) {
        try { const d = wCtx.createMediaStreamDestination(); ch._gate.connect(d); const s2 = mon.ctx.createMediaStreamSource(d.stream), g2 = mon.ctx.createGain(); g2.gain.value = 0.8; s2.connect(g2); g2.connect(mon.ctx.destination);
          const st0 = ch.stop; ch.stop = () => { try { s2.disconnect(); g2.disconnect(); ch._gate.disconnect(d); } catch (e) {} st0(); }; ch.monitored = true; } catch (e) {}
      }
      return ch;
    },
    voicePresets: ['natural', 'punch', 'contest'], voiceMon: false,
    /* Android: hold the foreground service + wake lock without the app's own sound (the REMOTE link), media volume to the top */
    keepAwake(on, maxVolume) { if (!NATIVE) return Promise.resolve({ held: false }); return KA.keepAwake({ on: !!on, maxVolume: !!maxVolume }).catch(() => ({ held: false })); },
    gain: 0.5, txing: false, onTx: null, onLost: null, pauseRx: false, session: 0, outDevId: ''   /* session = which sound start this is (Web Audio nodes die with their AudioContext) */
  };

  /* web fallback (Windows app + browsers): Web Audio with the call-mode processing turned off */
  let wSend = null, mon = { ctx: null, g: null, gen: 0 };
  let wCtx = null, wStream = null, wProc = null, wG = null, wSrc = null, wHist = new Float32Array(24), wPh = 0, FIR = null, wWorkURL = null;
  const stat = { how: '', blocks: 0, gaps: 0, anchors: 0, state: '', gen: 0 };   /* gen = which sound session (a restart = a new AudioContext: nodes from the old one are dead) */   /* for the builders' report: KPCNative.audio.capture() */
  /* the capture that runs on the audio thread: 48 kHz in → RMS/peak → 24-tap low-pass (5 kHz) + take every 4th sample → 12 kHz blocks of ~85 ms */
  const WORKLET_SRC = `
    class KpcCapture extends AudioWorkletProcessor {
      constructor() { super(); const N = 24, fc = 5000 / sampleRate, h = new Float32Array(N); let s = 0;
        for (let i = 0; i < N; i++) { const m = i - (N - 1) / 2, x = m === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * m) / (Math.PI * m); h[i] = x * (0.54 - 0.46 * Math.cos(2 * Math.PI * i / (N - 1))); s += h[i]; }
        for (let i = 0; i < N; i++) h[i] /= s; this.h = h; this.N = N;
        this.dec = sampleRate / 12000; this.hist = new Float32Array(N); this.out = new Float32Array(1024); this.k = 0; this.sum = 0; this.peak = 0; this.n = 0; this.frame0 = 0; this.next = 0; }
      process(inputs) {
        const ch = inputs[0] && inputs[0][0]; if (!ch) return true;
        /* Nov 18 full review (A2): any sound-card rate (44.1 kHz too) comes out at a TRUE 12 kHz: the filter is read at fractional
           positions (step = rate / 12000) with straight-line interpolation, the position carried over between blocks */
        const len = ch.length, N = this.N, h = this.h, x = new Float32Array(N + len); x.set(this.hist); x.set(ch, N);
        for (let i = 0; i < len; i++) { const v = ch[i]; this.sum += v * v; const a = v < 0 ? -v : v; if (a > this.peak) this.peak = a; }
        this.n += len;
        let p = this.next;                      /* position in this block of the next output sample (may be fractional, or -1…0 = from the last block) */
        const at = i => { let acc = 0; const q = N + i; for (let j = 0; j < N; j++) acc += h[j] * x[q - j]; return acc; };
        while (p < len - 1) {
          if (this.k === 0) this.frame0 = currentFrame + p;
          const i0 = Math.floor(p), fr = p - i0, a0 = at(i0);
          this.out[this.k++] = fr ? a0 + fr * (at(i0 + 1) - a0) : a0; p += this.dec;
          if (this.k >= this.out.length) this.flush();
        }
        this.next = p - len; this.hist = x.slice(len);
        return true;
      }
      flush() { if (!this.k) return; const db = 20 * Math.log10(Math.sqrt(this.sum / Math.max(1, this.n)) + 1e-9);
        this.port.postMessage({ pcm: this.out.slice(0, this.k), frame: this.frame0, n: this.k * this.dec, db: Math.round(db * 10) / 10, peak: Math.round(this.peak * 1000) / 1000 });
        this.k = 0; this.sum = 0; this.peak = 0; this.n = 0; }
    }
    registerProcessor('kpc-capture', KpcCapture);`;
  function fir() { if (FIR) return FIR; const N = 24, h = new Float32Array(N), fc = 5000 / RATE; let s = 0; for (let i = 0; i < N; i++) { const m = i - (N - 1) / 2, x = m === 0 ? 2 * fc : Math.sin(2 * Math.PI * fc * m) / (Math.PI * m); h[i] = x * (0.54 - 0.46 * Math.cos(2 * Math.PI * i / (N - 1))); s += h[i]; } for (let i = 0; i < N; i++) h[i] /= s; FIR = h; return h; }
  async function webStart(o) {
    await webStop(); stat.gen++; audio.session = stat.gen; stat.blocks = stat.gaps = stat.anchors = 0;
    const AC = G.AudioContext || G.webkitAudioContext; if (!AC || !navigator.mediaDevices) throw new Error('This browser has no sound support.');
    wCtx = new AC({ sampleRate: RATE }); if (wCtx.state === 'suspended') await wCtx.resume(); stat.state = wCtx.state; wSend = null;
    wG = wCtx.createGain(); wG.gain.value = audio.gain; wG.connect(wCtx.destination);
    audio.outDevId = o.output || ''; if (o.output && wCtx.setSinkId) { try { await wCtx.setSinkId(o.output); } catch (e) {} }
    const c = { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 }; if (o.input) c.deviceId = { exact: o.input };
    wStream = await navigator.mediaDevices.getUserMedia({ audio: c });
    /* Oct 26 (Fable; Brandon: 'lost sound, had to reopen'): a USB sound card that drops out ends its track, and Windows can suspend the
       AudioContext — say so (audio.onLost) so the app can start the sound again by itself */
    { const gen = stat.gen; wStream.getAudioTracks().forEach(t => { t.onended = () => { if (stat.gen === gen && wCtx && audio.onLost) audio.onLost('the sound device stopped (unplugged, or taken by Windows)'); }; });
    }
    const src = wCtx.createMediaStreamSource(wStream);
    /* Oct 25 (Fable; Brandon's PC: 'samples not ready' for ever, only 8,000 of every 12,000 samples arrived): the old capture was a
       ScriptProcessor on the PAGE's thread, and its blocks were time-stamped by COUNTING samples. When the page was busy or Windows
       put the window in the background, blocks were dropped and the count fell behind the clock, so an FT8 slot never 'finished'.
       Now: an AudioWorklet does the capture + the 12 kHz decimation on the AUDIO thread (never starved), and every block carries the
       audio clock's frame number; the page turns that into wall time anchored to the real clock (and re-anchors after a stall).
       The ScriptProcessor stays as a fallback for a browser with no AudioWorklet. */
    let worklet = false;
    if (wCtx.audioWorklet && G.Blob && G.URL) {
      try {
        if (!wWorkURL) wWorkURL = URL.createObjectURL(new Blob([WORKLET_SRC], { type: 'application/javascript' }));
        await wCtx.audioWorklet.addModule(wWorkURL);
        if (G.KPCNR) await KPCNR.prepare(wCtx);   /* Nov 6: ready for the remote link's cleaned-up sound */
        wProc = new AudioWorkletNode(wCtx, 'kpc-capture', { numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [1], channelCount: 1, channelCountMode: 'explicit' });
        const rate = wCtx.sampleRate; let base = 0, lastT = 0, lateN = 0;
        wProc.port.onmessage = e => {
          const m = e.data; if (!m || !m.pcm) return;
          const now = Date.now(), blockMs = m.n / rate * 1000, frameMs = m.frame / rate * 1000;
          /* wall time of audio frame 0 = the EARLIEST (now − frame time) ever seen: a block handed over late (busy page) cannot move it,
             only a block that arrives sooner can. If the audio clock itself stopped (device sleep, context suspended), every block
             then comes 'late' for good → after 12 such blocks the anchor moves up to the new truth. */
          const off = now - blockMs - frameMs;
          if (!base || off < base) { if (!base || base - off > 50) stat.anchors++; base = off; lateN = 0; }
          else if (off - base > 1000) { if (++lateN >= 12) { base = off; lateN = 0; stat.anchors++; } }
          else lateN = 0;
          const tStart = base + frameMs;
          if (lastT && tStart - lastT > blockMs * 1.5) stat.gaps++;
          lastT = tStart; stat.blocks++;
          if (onRx) onRx({ pcm: m.pcm, t: tStart, db: m.db, peak: m.peak, tx: !!wSrc });
        };
        worklet = true;
      } catch (e) { console.warn('AudioWorklet capture not available, using the old capture: ' + (e.message || e)); wProc = null; }
    }
    stat.how = worklet ? 'worklet' : 'script';
    if (!worklet) {
      const h = fir(); wProc = wCtx.createScriptProcessor(4096, 1, 1); let t0 = 0, n = 0;
      wProc.onaudioprocess = e => {
        const inp = e.inputBuffer.getChannelData(0), len = inp.length, rate = wCtx.sampleRate, now = Date.now();
        /* time by the wall clock, not by counting: a dropped block moves the clock on, so the decoder's slot still ends on time */
        const pred = t0 ? t0 + n / rate * 1000 : 0;
        if (!t0 || Math.abs(pred + len / rate * 1000 - now) > 400) { t0 = now - len / rate * 1000; n = 0; stat.anchors++; }
        const tStart = t0 + n / rate * 1000; n += len; stat.blocks++;
        let sum = 0, peak = 0; for (let i = 0; i < len; i++) { const v = inp[i]; sum += v * v; const a = v < 0 ? -v : v; if (a > peak) peak = a; }
        const db = 20 * Math.log10(Math.sqrt(sum / len) + 1e-9);
        const x = new Float32Array(24 + len); x.set(wHist); x.set(inp, 24);
        const step = rate / 12000, out = []; const at = i => { let acc = 0; const q = 24 + i; for (let j = 0; j < 24; j++) acc += h[j] * x[q - j]; return acc; };   /* Nov 18 (A2): a true 12 kHz at any rate */
        let p = wPh; while (p < len - 1) { const i0 = Math.floor(p), fr = p - i0, a0 = at(i0); out.push(fr ? a0 + fr * (at(i0 + 1) - a0) : a0); p += step; }
        wPh = p - len; wHist = x.slice(len); if (onRx) onRx({ pcm: Float32Array.from(out), t: tStart, db: Math.round(db * 10) / 10, peak: Math.round(peak * 1000) / 1000, tx: !!wSrc });
      };
    }
    src.connect(wProc); const sink = wCtx.createGain(); sink.gain.value = 0; wProc.connect(sink); sink.connect(wCtx.destination);
    { const gen = stat.gen, ctx = wCtx; ctx.onstatechange = () => { if (stat.gen !== gen) return; stat.state = ctx.state; if (ctx.state === 'suspended') ctx.resume().catch(() => {}); if (ctx.state === 'closed' && wCtx === ctx && audio.onLost) audio.onLost('the sound engine closed'); }; }
    return { ok: true, source: 'web', latencyMs: Math.round((wCtx.baseLatency || 0.02) * 1000), rate: wCtx.sampleRate };
  }
  async function webStop() { webStopTx(); if (mon.ctx) { try { mon.ctx.close(); } catch (e) {} mon.ctx = null; mon.g = null; } try { wProc && wProc.port && (wProc.port.onmessage = null); } catch (e) {} try { wProc && wProc.disconnect(); } catch (e) {} try { wStream && wStream.getTracks().forEach(t => t.stop()); } catch (e) {} try { wCtx && await wCtx.close(); } catch (e) {} wCtx = wStream = wProc = wG = null; }
  /* Nov 18 public-release review (0.9.7): a sound that is stopped must END its play() promise at once. Before, the promise only ended
     on the sound's own 'ended' event, which never comes once the sound engine is closed (STOP LISTENING, the sound card lost, the PC
     waking up): the voice keyer / CW / RTTY / SSTV / APRS waiting on it never reached its unkey, and the radio stayed keyed until
     the LONGEST TRANSMISSION timer. fin() runs once per sound, from whichever comes first: its end, stopTx(), or stop(). */
  function webPlay(pcm, atMs, id) {
    return new Promise((res, rej) => {
      if (!wCtx) { rej(new Error('Sound is not started.')); return; }
      webStopTx();
      const b = wCtx.createBuffer(1, pcm.length, RATE); b.copyToChannel(pcm, 0);
      const s = wCtx.createBufferSource(); s.buffer = b; s.connect(wG); wSrc = s;
      const at = atMs ? Math.max(0, (atMs - Date.now()) / 1000) : 0;
      let fin1 = false;
      s._fin = st => { if (fin1) return; fin1 = true; if (wSrc === s) wSrc = null; const ev = { state: st, id }; audio.txing = false; try { if (audio.onTx) audio.onTx(ev); } catch (e) {} res(ev); };
      s.onended = () => s._fin(s._stopped ? 'stopped' : 'end');
      audio.txing = true; if (audio.onTx) audio.onTx({ state: 'start', id }); s.start(wCtx.currentTime + at);
    });
  }
  function webStopTx() { if (wSrc) { const s = wSrc; wSrc = null; try { s._stopped = true; s.stop(); } catch (e) {} if (s._fin) s._fin('stopped'); } return Promise.resolve(); }
  /* Android: a sound still waiting for its start time is dropped by the plugin's stopTx() / stop() with no 'tx' event, so its promise is
     ended here ('stopped') if the plugin has not ended it itself by then. Only the waits that were open at the stop: a new sound with the
     same id is left alone. */
  function settleTx(ms) {
    const pend = Object.keys(txWait).map(k => [k, txWait[k]]); if (!pend.length) return;
    setTimeout(() => { for (const [k, w] of pend) if (txWait[k] === w) { delete txWait[k]; audio.txing = false; const ev = { state: 'stopped', id: k, late: true }; try { if (audio.onTx) audio.onTx(ev); } catch (e) {} w(ev); } }, ms);
  }

  /* ---------- USB radio (Android): looks like a Web Serial port to kpc-cat.js ---------- */
  function NativePort(info) { this.info = info; this.readable = null; this.writable = null; this.isNative = true; this.alive = false; }
  NativePort.prototype.getInfo = function () { return { usbVendorId: this.info.vid, usbProductId: this.info.pid, usbInterface: this.info.port, name: this.info.name, chip: this.info.chip }; };
  NativePort.prototype.open = async function (o) {
    o = o || {};
    await KS.open({ id: this.info.id, baud: +o.baudRate || 38400, dataBits: o.dataBits || 8, stopBits: o.stopBits || 1, parity: o.parity || 'none' });
    const q = []; let wake = null, closed = false; const self = this; this.alive = true;
    const kick = () => { if (wake) { const w = wake; wake = null; w(); } };
    this._h = await KS.addListener('data', ev => { q.push(b64toBytes(ev.data)); kick(); });
    this._e = await KS.addListener('error', ev => { closed = true; self.alive = false; self.lastError = ev && ev.message; kick(); });
    this._close = () => { closed = true; kick(); };
    this.readable = { getReader: () => ({
      read: async () => { while (!q.length && !closed) await new Promise(r => { wake = r; }); return q.length ? { value: q.shift(), done: false } : { value: undefined, done: true }; },
      cancel: async () => { closed = true; kick(); }, releaseLock: () => {} }) };
    this.writable = { getWriter: () => ({ write: bytes => KS.write({ data: bytesToB64(bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)) }), releaseLock: () => {} }) };
  };
  NativePort.prototype.setSignals = function (o) { const p = {}; if ('dataTerminalReady' in o) p.dtr = !!o.dataTerminalReady; if ('requestToSend' in o) p.rts = !!o.requestToSend; return KS.setSignals(p); };
  NativePort.prototype.close = async function () { this.alive = false; if (this._close) this._close(); try { this._h && this._h.remove(); this._e && this._e.remove(); } catch (e) {} this._h = this._e = null; try { await KS.close(); } catch (e) {} };
  let PORTS = [];
  const serial = NATIVE ? {
    async ports() { const r = await KS.list(); const out = (r.ports || []).map(i => { const old = PORTS.find(p => p.info.id === i.id); if (old) { old.info = i; return old; } return new NativePort(i); }); PORTS = out; return out; },
    list: () => KS.list().then(r => r.ports || []),
    letGo: () => KS.letGoNow().catch(() => ({})),   // drop the USB port before TX sound (the tablet mutes the radio's sound card while we hold it)
    holding: () => KS.isOpen().then(r => !!r.holding).catch(() => false)
  } : null;

  /* ---------- a WebSocket to the home PC (Android): the app's own socket, so the https page may open ws:// and failures say why ---------- */
  const KW = NATIVE ? C.registerPlugin('KpcWs') : null;
  const WSS = {}; let wsWired = false;
  function ws(url, ms) {
    if (!KW) { const w = new WebSocket(url); return w; }
    const o = { url, readyState: 0, onopen: null, onmessage: null, onclose: null, onerror: null, lastError: '', id: null,
      send(d) { if (o.id && o.readyState === 1) KW.send({ id: o.id, data: String(d) }).catch(() => {}); },
      close() { if (o.id) KW.close({ id: o.id }).catch(() => {}); o.readyState = 2; } };
    if (!wsWired) { wsWired = true;
      KW.addListener('open', ev => { const w = WSS[ev.id]; if (w) { w.readyState = 1; if (w.onopen) w.onopen({}); } });
      KW.addListener('message', ev => { const w = WSS[ev.id]; if (w && w.onmessage) w.onmessage({ data: ev.data }); });
      KW.addListener('error', ev => { const w = WSS[ev.id]; if (w) { w.lastError = ev.message || ''; if (w.onerror) w.onerror({ message: ev.message }); } });
      KW.addListener('close', ev => { const w = WSS[ev.id]; if (w) { w.readyState = 3; delete WSS[ev.id]; if (w.onclose) w.onclose({ code: ev.code, reason: ev.reason || w.lastError }); } });
    }
    KW.open({ url, ms: ms || 5000 }).then(r => { o.id = r.id; WSS[r.id] = o; if (o.readyState === 2) o.close(); }).catch(e => { o.lastError = String(e.message || e); o.readyState = 3; if (o.onerror) o.onerror({ message: o.lastError }); if (o.onclose) o.onclose({ code: 1006, reason: o.lastError }); });
    return o;
  }
  /* ---------- Bluetooth serial (Android): a paired TNC or CAT dongle, as a Web-Serial-like port ---------- */
  const KB = NATIVE ? C.registerPlugin('KpcBt') : null;
  function BtPort(info) { this.info = info; this.readable = null; this.writable = null; this.isBt = true; this.alive = false; }
  BtPort.prototype.getInfo = function () { return { name: '📶 ' + this.info.name, bt: this.info.id }; };
  BtPort.prototype.open = async function () {
    await KB.open({ id: this.info.id });
    const q = []; let wake = null, closed = false; const self = this; this.alive = true;
    const kick = () => { if (wake) { const w = wake; wake = null; w(); } };
    this._h = await KB.addListener('btdata', ev => { q.push(b64toBytes(ev.data)); kick(); });
    this._e = await KB.addListener('btclose', ev => { closed = true; self.alive = false; self.lastError = ev && ev.message; kick(); });
    this.readable = { getReader: () => ({ read: async () => { while (!q.length && !closed) await new Promise(r => { wake = r; }); return q.length ? { value: q.shift(), done: false } : { value: undefined, done: true }; }, cancel: async () => { closed = true; kick(); }, releaseLock: () => {} }) };
    this.writable = { getWriter: () => ({ write: bytes => KB.write({ data: bytesToB64(bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes)) }), releaseLock: () => {} }) };
    this._close = () => { closed = true; kick(); };
  };
  BtPort.prototype.setSignals = async function () {};
  BtPort.prototype.close = async function () { this.alive = false; if (this._close) this._close(); try { this._h && this._h.remove(); this._e && this._e.remove(); } catch (e) {} try { await KB.close(); } catch (e) {} };
  const bt = NATIVE ? { list: async () => { const r = await KB.list(); return (r.devices || []).map(d => new BtPort(d)); }, ok: true } : null;
  G.KPCNative = { _workletSrc: WORKLET_SRC, _ssbFir: ssbFir, _voiceChain: voiceChain, native: NATIVE, ws, bt, platform: NATIVE ? C.getPlatform() : (/Electron/i.test(navigator.userAgent) ? 'windows' : 'web'), audio, serial, b64toF32, f32toB64 };
})(window);
