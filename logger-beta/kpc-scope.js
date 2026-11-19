/* KPC app: 🌊 SCOPE — a real waterfall on the RADIO screen and under the contest band map (Nov 6 2026, Opus; Brandon: 'add the
   waterfall where you can see who is where' + the SDR handoff; his radios: IC-7300, IC-7100, FT-710, FTDX10, FT-891, FTX-1).

   WHERE THE PICTURE COMES FROM — and it always SAYS which (the handoff: 'an audio FFT is an AF spectrum, not an RF panadapter'):
     RF  · Icom scope over CI-V (IC-7300, IC-705, IC-9700, IC-7610, IC-905): command 27 00 'scope waveform data'. The radio sends
           the scope it draws on its own screen: 475 points, 0-160 each, in 11 pieces over USB (piece 1 = mode + edges, 2-11 = the
           wave). Turned on with 27 10 01 (scope ON) + 27 11 01 (send the data); off with 27 11 00. kpc-cat.js hands every byte it
           reads through KPCScope.tap() FIRST, which lifts the 27 00 frames out, so the dial / meter / keyer reads never see them.
           Radio menu: SET > Connectors > CI-V > CI-V USB Port = 'Unlink from [REMOTE]', CI-V USB Baud Rate = 115200.
     AF  · every other radio (IC-7100, FT-710, FTDX10, FT-891, FTX-1, …): the radio's USB SOUND, the same blocks the FT8 decoder
           gets (AP 'rx', 12 kHz). Labelled AUDIO (Hz): it only shows what is inside the radio's receive filter, never the band.
           (The FT-710's real scope needs its separate FT4222 USB port + FTDI driver: a later step.)
     SIM · the pretend radio (?fake=1): a made-up RF scope with a carrier at each spot, so the screens and the tests work with no rig.
   Two stores: ROWS (every frame, ~30 s) for the RADIO screen; SLOW (one row per 2 s, 10 minutes) for the contest band map, so the
   real signals sit under the skimmer marks. Labels on the picture come from SPOTS (internet) and say so: a peak alone never names a station. */
(function (G) {
  'use strict';
  const AP = G.KPCApp; if (!AP) return;
  const $ = id => document.getElementById(id), esc = AP.esc;
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SV = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const S = Object.assign({ on: true, civSpan: 25000, civMode: 0, contrast: 1, afHi: 3000, pitch: 600 }, LS('kpcAppScope', {}));
  /* Nov 19 2026 (Brandon: 'great looking scope with who is where and park number, all turn on or off'): what the picture shows, each a
     switch on the scope's SHOW row. spots = name tags at all; calls / park = what a tag says; sota = SOTA summits; rbn = skimmer-only
     calls (no human spot); plan = my licence class's band plan behind the trace; grid = lines; peak = a slow-falling peak line;
     pass = my receive filter shaded on the picture. */
  S.show = Object.assign({ spots: 1, calls: 1, park: 1, sota: 1, rbn: 0, plan: 1, grid: 1, peak: 1, pass: 1 }, S.show || {});
  const save = () => SV('kpcAppScope', S);
  const CIV_SCOPE = { ic7300: 1, ic705: 1, ic9700: 1, ic7610: 1, ic905: 1 };

  /* ======================================================================== the rows */
  const ROWS = [], SLOW = [], MAXR = 400;
  const ST = { src: '', what: '', n: 0, last: 0, fps: 0, err: '', mode: '', oor: false, lo: 0, hi: 0 };
  let fpsN = 0, fpsT = Date.now(), slowCur = null;
  const subs = new Set();
  function push(row) {
    ROWS.push(row); if (ROWS.length > MAXR) ROWS.splice(0, ROWS.length - MAXR);
    ST.n++; ST.last = row.t; ST.src = row.src; ST.lo = row.lo; ST.hi = row.hi;
    fpsN++; if (row.t - fpsT >= 2000) { ST.fps = Math.round(fpsN * 1000 / (row.t - fpsT)); fpsN = 0; fpsT = row.t; }
    if (row.src !== 'af') {                       /* the band map gets RF only: one row per 2 s = the loudest of those 2 s */
      if (!slowCur || row.t - slowCur.t >= 2000 || slowCur.lo !== row.lo || slowCur.hi !== row.hi || slowCur.v.length !== row.v.length) {
        slowCur = { t: row.t, lo: row.lo, hi: row.hi, v: Float32Array.from(row.v), src: row.src }; SLOW.push(slowCur);
        const cut = row.t - 10 * 60000; while (SLOW.length && SLOW[0].t < cut) SLOW.shift(); if (SLOW.length > 400) SLOW.shift();
      } else for (let i = 0; i < row.v.length; i++) if (row.v[i] > slowCur.v[i]) slowCur.v[i] = row.v[i];
    }
    subs.forEach(f => { try { f(row); } catch (e) {} });
  }

  /* ======================================================================== RF: Icom CI-V scope (27 00) */
  const bcd = x => (x >> 4) * 10 + (x & 15);
  const hzLE = a => { let s = ''; for (let j = a.length - 1; j >= 0; j--) s += bcd(a[j]).toString().padStart(2, '0'); return +s; };
  const bcdLE = (n, len) => { const s = String(Math.round(n)).padStart(len * 2, '0'); const o = []; for (let j = len - 1; j >= 0; j--) o.push(parseInt(s.substr(j * 2, 2), 16)); return o; };
  let CUR = null, pend = [];
  function civFrame(d) {
    if (!d || d.length < 3 || d[0] !== 0) return;          /* d[0] = 00 main scope (a 9700 / 7610's sub scope = 01: not shown) */
    const seq = bcd(d[1]), max = bcd(d[2]);
    if (seq === 1) {
      if (d.length < 15) return;
      const mode = d[3], f1 = hzLE(d.slice(4, 9)), f2 = hzLE(d.slice(9, 14)), oor = d[14] === 1;
      const center = mode === 0 || mode === 2;
      CUR = { max, lo: center ? f1 - f2 : f1, hi: center ? f1 + f2 : f2, mode, oor, wave: [] };
      ST.mode = ['CENTER', 'FIXED', 'SCROLL-C', 'SCROLL-F'][mode] || ''; ST.oor = oor;
      if (d.length > 15) CUR.wave.push(...d.slice(15));   /* over LAN (max = 1) everything comes in one frame */
    } else if (CUR && seq > 1) CUR.wave.push(...d.slice(3));
    if (CUR && seq === max) {
      if (!CUR.oor && CUR.wave.length >= 50 && CUR.hi > CUR.lo) {
        const v = new Float32Array(CUR.wave.length); for (let i = 0; i < v.length; i++) v[i] = Math.min(1, CUR.wave[i] / 160);
        push({ t: Date.now(), lo: CUR.lo / 1000, hi: CUR.hi / 1000, v, src: 'civ' });
      }
      CUR = null;
    }
  }
  /* kpc-cat.js calls this with every chunk the radio sends (Icom only): scope frames come out, everything else goes on.
     A frame = FE FE <to> <from> <cmd> … FD (more leading FEs are allowed). A frame cut across two chunks waits for the rest. */
  function tap(chunk) {
    const b = pend.length ? pend.concat(Array.from(chunk)) : Array.from(chunk); pend = [];
    const out = []; let i = 0;
    while (i < b.length) {
      if (b[i] === 0xFE && i === b.length - 1) { pend = [0xFE]; break; }   /* a frame's first FE at the very end of a chunk */
      if (b[i] === 0xFE && b[i + 1] === 0xFE) {
        const end = b.indexOf(0xFD, i + 2);
        if (end < 0) { if (b.length - i > 1500) { out.push(...b.slice(i)); i = b.length; } else { pend = b.slice(i); } break; }
        let s = i; while (s + 2 < end && b[s + 2] === 0xFE) s++;
        if (b[s + 4] === 0x27 && b[s + 5] === 0x00 && b[s + 3] !== 0xE0) civFrame(b.slice(s + 6, end));   /* from the radio (not our own echo) */
        else for (let k = i; k <= end; k++) out.push(b[k]);
        i = end + 1;
      } else { out.push(b[i]); i++; }
    }
    return out;
  }
  const radioId = () => (G.KPCCat && KPCCat.get().radio) || '';
  const hasCiv = () => !!(G.KPCCat && KPCCat.get().proto === 'icom' && CIV_SCOPE[radioId()] && KPCCat.link() === 'serial' && KPCCat.connected());
  const civBytes = body => { const a = parseInt((KPCCat.get().civ || '94'), 16) & 255; return new Uint8Array([0xFE, 0xFE, a, 0xE0, ...body, 0xFD]); };
  let civOn = false;
  async function civStart() {
    if (!hasCiv() || !KPCCat.raw) return false;
    const ok = await KPCCat.raw(civBytes([0x27, 0x10, 0x01])) && await KPCCat.raw(civBytes([0x27, 0x11, 0x01]));
    civOn = !!ok; ST.err = ok ? '' : 'the radio did not take the scope commands'; return civOn;
  }
  async function civStop() { if (civOn && G.KPCCat && KPCCat.raw && KPCCat.connected()) await KPCCat.raw(civBytes([0x27, 0x11, 0x00])); civOn = false; }
  async function civSpan(hz) { S.civSpan = hz; save(); if (hasCiv()) { await KPCCat.raw(civBytes([0x27, 0x14, 0x00, 0x00])); await KPCCat.raw(civBytes([0x27, 0x15, 0x00, ...bcdLE(hz, 5)])); } }
  async function civFixed() { if (hasCiv()) await KPCCat.raw(civBytes([0x27, 0x14, 0x00, 0x01])); }

  /* ======================================================================== AF: the radio's USB sound (any radio) */
  const AFN = 2048, AFR = 12000, AFB = AFR / AFN;
  const aw = new Float32Array(AFN), are = new Float32Array(AFN), aim = new Float32Array(AFN), arev = new Uint16Array(AFN);
  for (let i = 0; i < AFN; i++) { aw[i] = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (AFN - 1)); let r = 0; for (let k = 0; k < 11; k++) if (i & (1 << k)) r |= 1 << (10 - k); arev[i] = r; }
  function afft() {
    for (let i = 0; i < AFN; i++) { const j = arev[i]; if (j > i) { let t = are[i]; are[i] = are[j]; are[j] = t; t = aim[i]; aim[i] = aim[j]; aim[j] = t; } }
    for (let len = 2; len <= AFN; len <<= 1) { const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang), h = len >> 1;
      for (let i = 0; i < AFN; i += len) { let cr = 1, ci = 0; for (let k = 0; k < h; k++) { const ar = are[i + k], ai = aim[i + k], br = are[i + k + h], bi = aim[i + k + h], vr = br * cr - bi * ci, vi = br * ci + bi * cr;
        are[i + k] = ar + vr; aim[i + k] = ai + vi; are[i + k + h] = ar - vr; aim[i + k + h] = ai - vi; const nr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = nr; } } }
  }
  const ring = new Float32Array(AFN); let rpos = 0, rfill = 0, afT = 0, afFloor = -90, afTop = -30;
  function afBlock(c) {
    const p = c && c.pcm; if (!p || !S.on || civOn || simOn() || f7Fresh()) return;
    for (let i = 0; i < p.length; i++) { ring[rpos] = p[i]; rpos = (rpos + 1) % AFN; } rfill += p.length;
    const now = Date.now(); if (rfill < AFN || now - afT < 90) return; afT = now;
    for (let i = 0; i < AFN; i++) { are[i] = ring[(rpos + i) % AFN] * aw[i]; aim[i] = 0; }
    afft();
    const lo = 100, hi = Math.min(5800, S.afHi || 3000), a = Math.round(lo / AFB), b = Math.round(hi / AFB), n = b - a, v = new Float32Array(n);
    let mx = -200, sum = 0;
    for (let i = 0; i < n; i++) { const k = a + i, d = 10 * Math.log10(are[k] * are[k] + aim[k] * aim[k] + 1e-14); v[i] = d; sum += d; if (d > mx) mx = d; }
    const avg = sum / n; afFloor = afFloor * 0.95 + (avg - 3) * 0.05; afTop = afTop * 0.9 + Math.max(mx, afFloor + 25) * 0.1;
    const span = Math.max(20, afTop - afFloor) / (S.contrast || 1);
    for (let i = 0; i < n; i++) v[i] = Math.max(0, Math.min(1, (v[i] - afFloor) / span));
    push({ t: now, lo, hi, v, src: 'af', hz: true });
  }
  AP.on('rx', afBlock);

  /* ======================================================================== SIM: the pretend radio */
  const simOn = () => !!(G.KPCCat && KPCCat.link() === 'fake' && KPCCat.connected());
  let simT = null;
  function simTick() {
    if (!S.on || !simOn()) return;
    const dk = (G.KPCLog && KPCLog.dock) || {}, c = (KPCCat.fake && +KPCCat.fake().khz) || +dk.khz || 14074, span = (S.civSpan || 25000) / 1000, lo = c - span, hi = c + span, N = 475, v = new Float32Array(N);
    const sig = [];
    (G.KPCSpots ? KPCSpots.all() : []).forEach(s => { if (s.khz > lo && s.khz < hi) sig.push([s.khz, 0.55 + (s.call.charCodeAt(1) % 5) * 0.08]); });
    (G.KPCSkim ? KPCSkim.spots() : []).forEach(a => { if (a.khz > lo && a.khz < hi) sig.push([a.khz, 0.45 + Math.min(0.4, a.reps.size * 0.08)]); });
    for (let i = 0; i < N; i++) { const f = lo + i / (N - 1) * (hi - lo); let x = 0.12 + Math.random() * 0.08; sig.forEach(([k, a]) => { const d = Math.abs(f - k) / (span / N * 2.2); if (d < 3) x = Math.max(x, a * Math.exp(-d * d) * (0.85 + Math.random() * 0.15)); }); v[i] = x; }
    push({ t: Date.now(), lo, hi, v, src: 'sim' });
  }
  setInterval(() => { if (simOn() && S.on) { if (!simT) simT = setInterval(simTick, 120); } else if (simT) { clearInterval(simT); simT = null; } }, 1000);

  /* ======================================================================== RF: the FT-710's own scope (Nov 18)
     Its separate FT4222 USB port (radio menu SCU-LAN10 = ON), read by the Windows app's Python helper (electron/ft710.js +
     ft710_bridge.py; clean-room, from the tests on Brandon's FT-710, Nov 17). 851 points a line, ~28 lines a second; value =
     127 − (byte & 0x7F) (bigger = stronger). The picture is centred on the dial (the radio's scope in CENTER) and is about
     1.065 × the radio's SPAN wide (measured: 79 points per 10 kHz at SPAN 100 kHz, 40 at 200). The radio does not tell the
     app its SPAN, so the SPAN chips here must match the radio's. Windows app only: no FT4222 driver on Android or in a browser. */
  const F7 = { on: false, last: 0, err: '', floor: 18, n: 0 };
  let TUNE_HOOK = null;
  const phones = () => !!(G.KPCRemote && KPCRemote.base && KPCRemote.clients && KPCRemote.clients().length);   /* a phone on the remote link gets the waterfall too */
  const f7Radio = () => !!(G.KPCCat && KPCCat.get().radio === 'ft710');
  const f7Fresh = () => Date.now() - F7.last < 2000;
  function f7Row(b64) {
    let bin; try { bin = atob(b64); } catch (e) { return; }
    const n = bin.length; if (n < 100) return;
    const raw = new Float32Array(n); for (let i = 0; i < n; i++) raw[i] = 127 - (bin.charCodeAt(i) & 0x7F);
    const srt = Array.from(raw.subarray(4)).sort((a, b) => a - b); F7.floor = F7.floor * 0.9 + srt[srt.length >> 1] * 0.1;
    const fl = F7.floor + 2, v = new Float32Array(n); for (let i = 0; i < n; i++) v[i] = Math.max(0, Math.min(1, (raw[i] - fl) / 40));
    const ld = G.KPCCat && KPCCat.lastDial && KPCCat.lastDial(), dk = (G.KPCLog && KPCLog.dock) || {}, c = (ld && +ld.khz) || +dk.khz || 14074;
    const w = (+S.f7Span || 100) * 1.065;
    F7.last = Date.now(); F7.n++; F7.err = '';
    push({ t: F7.last, lo: c - w / 2, hi: c + w / 2, v, src: 'ft710' });
  }
  if (G.kpcFt710) { try { G.kpcFt710.onRow(f7Row); G.kpcFt710.onState(st => { F7.err = (st && st.err) || ''; if (st && !st.on) F7.on = false; }); } catch (e) {} }
  setInterval(() => {
    if (!G.kpcFt710) return;
    const want = S.on && f7Radio() && G.KPCCat && KPCCat.connected() && (/^(radio|contest|digi)$/.test(document.body.dataset.screen || '') || phones());
    if (want && !F7.on && !F7.err) { F7.on = true; G.kpcFt710.start().then(st => { if (st && st.err) F7.err = st.err; }).catch(e => { F7.err = String(e.message || e); F7.on = false; }); }
    else if (!want && F7.on) { F7.on = false; G.kpcFt710.stop().catch(() => {}); }
  }, 1500);
  /* start / stop the radio's scope with the CAT link and the switch */
  setInterval(() => { const want = S.on && hasCiv() && (document.body.dataset.screen === 'radio' || document.body.dataset.screen === 'contest' || phones()); if (want && !civOn) civStart(); else if (!want && civOn) civStop(); }, 1500);

  /* ======================================================================== drawing */
  /* Nov 18 (Brandon, the SDR mockup: 'nailed the waterfall'): a BLACK floor, then deep blue, blue, cyan, green, yellow, orange: the noise
     stays near black and only signals light up (the old floor was navy, which washed the picture out) */
  const STOPS = [[0, 0, 0, 0], [.22, 2, 8, 30], [.40, 10, 40, 130], [.55, 25, 120, 230], [.68, 50, 210, 220], [.80, 120, 240, 110], [.91, 255, 225, 60], [1, 255, 140, 30]];
  const LUT = (() => { const t = new Uint8Array(256 * 3); for (let i = 0; i < 256; i++) { const x = i / 255; let a = STOPS[0], b = STOPS[STOPS.length - 1]; for (let k = 0; k < STOPS.length - 1; k++) if (x >= STOPS[k][0] && x <= STOPS[k + 1][0]) { a = STOPS[k]; b = STOPS[k + 1]; break; } const f = b[0] === a[0] ? 0 : (x - a[0]) / (b[0] - a[0]); for (let c = 0; c < 3; c++) t[i * 3 + c] = a[c + 1] + (b[c + 1] - a[c + 1]) * f; } return t; })();
  const colOf = x => { const i = Math.max(0, Math.min(255, Math.round(x * 255))) * 3; return [LUT[i], LUT[i + 1], LUT[i + 2]]; };
  const valAt = (row, k) => { const n = row.v.length; const p = (k - row.lo) / (row.hi - row.lo) * (n - 1); if (p < 0 || p > n - 1) return -1; return row.v[Math.round(p)]; };

  /* under the contest band map (kpc-skim.js drawMap): the 2-second RF rows, time-aligned with the skimmer marks (newest at the top) */
  let UL = { c: null, key: '', at: 0 };
  function underlay(ctx, lo, hi, top, W, H, depthMs) {
    if (!SLOW.length || !S.on) return false;
    const now = Date.now(), last = SLOW[SLOW.length - 1]; if (now - last.t > 60000) return false;
    const key = lo.toFixed(2) + '|' + hi.toFixed(2) + '|' + W + '|' + H;
    if (!UL.c) UL.c = document.createElement('canvas');
    if (UL.key !== key || now - UL.at > 1000) {
      const c = UL.c; c.width = Math.max(1, Math.round(W / 2)); c.height = Math.max(1, Math.round(H / 2));
      const g = c.getContext('2d'), img = g.createImageData(c.width, c.height), d = img.data, rowH = Math.max(1, 2000 / depthMs * c.height);
      for (const r of SLOW) {
        const y0 = Math.floor((now - r.t) / depthMs * c.height); if (y0 >= c.height) continue;
        for (let x = 0; x < c.width; x++) { const v = valAt(r, lo + x / c.width * (hi - lo)); if (v < 0) continue; const [R, Gc, B] = colOf(v);
          for (let y = Math.max(0, y0 - Math.ceil(rowH)); y <= y0 && y < c.height; y++) { const o = (y * c.width + x) * 4; d[o] = R; d[o + 1] = Gc; d[o + 2] = B; d[o + 3] = 150; } }
      }
      g.putImageData(img, 0, 0); UL.key = key; UL.at = now;
    }
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.drawImage(UL.c, 0, top, W, H); ctx.restore();
    return true;
  }

  /* the RADIO screen widget: a spectrum line on top, the waterfall under it, a scale, spot labels; tap = tune */
  let W1 = null;
  function mount(cv) {
    if (W1 && W1.cv === cv) return; if (W1) W1.stop = true;
    const w = W1 = { cv, stop: false, img: null, lastN: 0, hits: [] };
    cv.onclick = ev => {
      const r = ROWS[ROWS.length - 1]; if (!r) return;
      const b = cv.getBoundingClientRect(), x = ev.clientX - b.left, y = ev.clientY - b.top;
      const h = w.hits.find(q => x >= q.x && x <= q.x + q.w && y >= q.y && y <= q.y + q.h);
      if (h && G.KPCSpots) { KPCSpots.tune(h.s); return; }
      const f = r.lo + x / b.width * (r.hi - r.lo);
      if (r.src === 'af') {
        const dk = (G.KPCLog && KPCLog.dock) || {}, md = String(dk.mode || '').toUpperCase(), sign = /LSB|DATAL/.test(md) ? -1 : 1;
        if (md === 'CW' && G.KPCCat && KPCCat.connected()) { KPCCat.tune(+dk.khz + (f - (S.pitch || 600)) / 1000, 'CW'); AP.toast('📻 Moved the dial onto that CW signal.', 2000, 'log'); return; }
        AP.toast('That sound is at ' + Math.round(f) + ' Hz ≈ ' + ((+dk.khz + sign * f / 1000) / 1000).toFixed(4) + ' MHz. (Audio picture: tap-to-tune works on CW here, and on the RF scope.)', 4000);
        return;
      }
      if (TUNE_HOOK) { TUNE_HOOK(Math.round(f * 10) / 10); return; }   /* Nov 18: the phone on the remote link tunes the PC's radio */
      if (G.KPCCat && KPCCat.connected()) { const dk = (G.KPCLog && KPCLog.dock) || {}; KPCCat.tune(Math.round(f * 10) / 10, dk.mode || 'USB'); }
    };
    const loop = () => { if (w.stop || !cv.isConnected) return; drawW(w); requestAnimationFrame(loop); };
    requestAnimationFrame(loop);
  }
  function drawW(w) {
    const cv = w.cv, dpr = G.devicePixelRatio || 1, Wd = cv.clientWidth, Hd = cv.clientHeight; if (!Wd || !Hd) return;
    if (cv.width !== Math.round(Wd * dpr) || cv.height !== Math.round(Hd * dpr)) { cv.width = Math.round(Wd * dpr); cv.height = Math.round(Hd * dpr); w.img = null; w.lastN = 0; }
    const g = cv.getContext('2d'), CW = cv.width, CH = cv.height, SPH = Math.round(CH * 0.3), AXH = Math.round(16 * dpr), WT = SPH + AXH, WH = CH - WT;
    const r = ROWS[ROWS.length - 1];
    g.fillStyle = '#000'; g.fillRect(0, 0, CW, SPH + AXH);   /* Nov 18: black, like the radio's own scope */
    if (!r) { g.fillStyle = '#05080f'; g.fillRect(0, 0, CW, CH); g.fillStyle = '#9AA6B5'; g.font = (13 * dpr) + 'px sans-serif'; g.textAlign = 'center'; g.fillText(status().line, CW / 2, CH / 2); return; }
    /* waterfall: scroll by the number of new rows, paint them at the top */
    if (!w.img || w.img.width !== CW || w.img.height !== WH) { w.img = g.createImageData(CW, WH); w.lastN = ST.n; for (let i = 3; i < w.img.data.length; i += 4) w.img.data[i] = 255; }
    const rp = Math.max(1, Math.round(2 * dpr));   /* each row = 2 px (about 15 s of history on a 7300) */
    const nNew = Math.min(Math.ceil(WH / rp), ST.n - w.lastN); w.lastN = ST.n;
    if (nNew > 0) {
      const d = w.img.data, rowB = CW * 4, sh = Math.min(WH, nNew * rp); d.copyWithin(sh * rowB, 0, (WH - sh) * rowB);
      for (let k = 0; k < nNew; k++) { const row = ROWS[ROWS.length - 1 - k]; if (!row) break;
        for (let x = 0; x < CW; x++) { const v = row.v[Math.min(row.v.length - 1, Math.floor(x / CW * row.v.length))]; const [R, Gc, B] = colOf(Math.min(1, v * (S.contrast || 1)));
          for (let yy = k * rp; yy < (k + 1) * rp && yy < WH; yy++) { const o = yy * rowB + x * 4; d[o] = R; d[o + 1] = Gc; d[o + 2] = B; d[o + 3] = 255; } } }
    }
    g.putImageData(w.img, 0, WT);
    /* ---- the top part: band plan, grid, my filter, the trace + its peak line, the scale, my dial, the name tags (Nov 19 2026) ---- */
    const span = r.hi - r.lo, X = k => (k - r.lo) / span * CW, rf = r.src !== 'af', SW = S.show, TAGH = rf && SW.spots ? Math.round(32 * dpr) : 0;
    const dk = (G.KPCLog && KPCLog.dock) || {}, ld = G.KPCCat && KPCCat.lastDial && KPCCat.lastDial(), rk = simOn() ? +KPCCat.fake().khz : (ld && +ld.khz) || +dk.khz;
    const md = String((ld && ld.mode) || dk.mode || '').toUpperCase();
    if (rf && SW.plan && AP.bandPlan && AP.bandPlan.segments) {   /* my licence class: CW/data blue, phone amber, data purple; not mine = nothing */
      for (const sg of AP.bandPlan.segments(AP.S.cls || 'E')) { if (sg[1] <= r.lo || sg[0] >= r.hi) continue; const k2 = sg[3];
        g.fillStyle = /ph/.test(k2) ? 'rgba(232,184,74,.07)' : /dig|data/.test(k2) ? 'rgba(190,120,255,.08)' : /cw/.test(k2) ? 'rgba(109,180,245,.07)' : 'rgba(95,211,155,.06)';
        const x0 = Math.max(0, X(sg[0])), x1 = Math.min(CW, X(sg[1])); g.fillRect(x0, TAGH, x1 - x0, SPH - TAGH); } }
    if (SW.grid) { g.strokeStyle = 'rgba(255,255,255,.06)'; g.lineWidth = 1; for (let i = 1; i < 4; i++) { const y = TAGH + (SPH - TAGH) * i / 4; g.beginPath(); g.moveTo(0, y); g.lineTo(CW, y); g.stroke(); } }
    if (rf && SW.pass && rk >= r.lo && rk <= r.hi) {   /* what I hear: the filter beside the dial (USB above, LSB below, CW / AM around it) */
      const wkhz = (/CW/.test(md) ? 0.5 : /AM|FM/.test(md) ? 6 : 2.4), a0 = /LSB|DATAL/.test(md) ? rk - wkhz : /CW|AM|FM/.test(md) ? rk - wkhz / 2 : rk, a1 = a0 + wkhz;
      g.fillStyle = 'rgba(255,182,72,.10)'; g.fillRect(X(a0), TAGH, X(a1) - X(a0), CH - TAGH); }
    const pts = new Float32Array(CW); for (let x = 0; x < CW; x++) pts[x] = r.v[Math.min(r.v.length - 1, Math.floor(x / CW * r.v.length))];
    const yOf = v => SPH - 2 - v * (SPH - TAGH - 6);
    if (SW.peak) { if (!w.pk || w.pk.length !== CW || w.pkLo !== r.lo || w.pkHi !== r.hi) { w.pk = Float32Array.from(pts); w.pkLo = r.lo; w.pkHi = r.hi; } for (let x = 0; x < CW; x++) w.pk[x] = Math.max(pts[x], w.pk[x] - 0.004);
      g.beginPath(); for (let x = 0; x < CW; x++) { const y = yOf(w.pk[x]); if (x) g.lineTo(x, y); else g.moveTo(x, y); } g.strokeStyle = 'rgba(255,182,72,.38)'; g.lineWidth = dpr; g.stroke(); }
    g.beginPath(); for (let x = 0; x < CW; x++) { const y = yOf(pts[x]); if (x) g.lineTo(x, y); else g.moveTo(x, y); }
    const line = rf ? '#9fe6ff' : '#8fd3ff'; g.strokeStyle = line; g.lineWidth = 1.2 * dpr; g.shadowColor = '#5fd0ff'; g.shadowBlur = 6 * dpr; g.stroke(); g.shadowBlur = 0;
    g.lineTo(CW, SPH); g.lineTo(0, SPH); g.closePath(); const gr = g.createLinearGradient(0, TAGH, 0, SPH); gr.addColorStop(0, 'rgba(120,220,255,.5)'); gr.addColorStop(1, 'rgba(20,60,120,.04)'); g.fillStyle = gr; g.fill();
    /* scale */
    g.fillStyle = '#05070a'; g.fillRect(0, SPH, CW, AXH); g.fillStyle = '#9AA6B5'; g.font = '700 ' + (10 * dpr) + 'px ui-monospace,monospace'; g.textAlign = 'center'; g.strokeStyle = 'rgba(150,150,150,.4)';
    const steps = rf ? [0.5, 1, 2, 5, 10, 25, 50, 100] : [100, 250, 500, 1000], st = steps.find(q => span / q <= Wd / 70) || steps[steps.length - 1];
    for (let f = Math.ceil(r.lo / st) * st; f <= r.hi; f += st) { const x = X(f); g.beginPath(); g.moveTo(x, SPH); g.lineTo(x, SPH + 4 * dpr); g.stroke(); g.fillText(!rf ? String(Math.round(f)) : (f / 1000).toFixed(st < 1 ? 4 : 3), x, SPH + 13 * dpr);
      if (SW.grid) { g.save(); g.strokeStyle = 'rgba(255,255,255,.06)'; g.beginPath(); g.moveTo(x, TAGH); g.lineTo(x, SPH); g.stroke(); g.restore(); } }
    /* the dial */
    if (rf && rk >= r.lo && rk <= r.hi) { const x = X(rk); g.strokeStyle = '#ff4d5e'; g.lineWidth = 1.5 * dpr; g.shadowColor = '#ff4d5e'; g.shadowBlur = 8 * dpr; g.beginPath(); g.moveTo(x, TAGH); g.lineTo(x, CH); g.stroke(); g.shadowBlur = 0; }
    /* name tags (RF only, from the internet: a spot, never 'heard'): call + park number, coloured by kind; two lanes, then they wait */
    w.hits = []; w.tags = 0;
    if (rf && SW.spots) {
      const band = G.KPCLog && KPCLog.band ? KPCLog.band(rk || (r.lo + r.hi) / 2) : '', list = G.KPCSkim && band ? KPCSkim.mapSpots(band) : [];
      const me = String((AP.me && AP.me().call) || AP.S.call || '').toUpperCase();
      g.font = '800 ' + (10 * dpr) + 'px ui-monospace,monospace'; g.textAlign = 'left'; const lanes = [0, 0];
      for (const sp of list) {
        if (sp.khz < r.lo || sp.khz > r.hi) continue;
        const refs = sp.refs || [], sota = refs.some(x => /\//.test(x)), wwff = refs.some(x => /^[A-Z0-9]*FF-/.test(x)), park = refs.some(x => /^[A-Z]{1,3}-\d{4,5}$/.test(x)), mine = me && sp.call === me;
        if (sp.src === 'rbn' && !SW.rbn) continue; if (sota && !park && !SW.sota) continue;
        const parts = []; if (SW.calls || !refs.length) parts.push(sp.call); if (SW.park && refs.length) parts.push(refs.slice(0, 2).join(' + ') + (refs.length > 2 ? ' +' + (refs.length - 2) : ''));
        const icon = mine ? '● ' : park ? '🌲 ' : sota ? '▲ ' : wwff ? '🌳 ' : sp.src === 'rbn' ? '◦ ' : '◇ ', lab = icon + parts.join('  ');
        const x = X(sp.khz), tw = g.measureText(lab).width + 8 * dpr, bx = Math.max(0, Math.min(x - 4 * dpr, g.canvas.width - tw));   /* a tag near the right edge slides left to stay whole */
        let ln = lanes.findIndex(e => e < bx); if (ln === -1) continue; lanes[ln] = bx + tw + 4 * dpr;
        const y = 2 * dpr + ln * 15 * dpr, bg = mine ? 'rgba(220,50,70,.92)' : park ? 'rgba(28,105,58,.92)' : sota ? 'rgba(130,80,210,.92)' : wwff ? 'rgba(20,110,120,.92)' : sp.src === 'rbn' ? 'rgba(60,66,76,.9)' : 'rgba(40,70,110,.92)';
        g.fillStyle = bg; if (g.roundRect) { g.beginPath(); g.roundRect(bx, y, tw, 13 * dpr, 3 * dpr); g.fill(); } else g.fillRect(bx, y, tw, 13 * dpr);
        g.fillStyle = '#fff'; g.fillText(lab, bx + 4 * dpr, y + 10 * dpr);
        g.strokeStyle = bg; g.setLineDash([2 * dpr, 2 * dpr]); g.beginPath(); g.moveTo(x, y + 13 * dpr); g.lineTo(x, TAGH); g.stroke(); g.setLineDash([]);
        w.hits.push({ x: bx / dpr, y: y / dpr, w: tw / dpr, h: 13, s: sp }); w.tags++;
      }
    }
  }
  function status() {
    const r = ROWS[ROWS.length - 1], fresh = r && Date.now() - r.t < 4000, id = radioId(), cat = G.KPCCat && KPCCat.connected();
    if (!S.on) return { cls: '', line: 'Scope is off.' };
    if (fresh && r.src === 'civ') return { cls: 'ok', line: '📡 RF scope from the radio · ' + ST.mode + ' · ' + r.lo.toFixed(1) + '–' + r.hi.toFixed(1) + ' kHz · ' + ST.fps + ' a second · ◇ = a spot from the internet, not heard here' };
    if (fresh && r.src === 'ft710') return { cls: 'ok', line: '📡 RF scope from the FT-710 (its own USB port) · SPAN ' + (+S.f7Span || 100) + ' kHz: set the same SPAN on the radio, scope in CENTER · ◇ = a spot from the internet, not heard here' };
    if (f7Radio() && F7.err) return { cls: 'warn', line: 'FT-710 scope: ' + F7.err };
    if (f7Radio() && G.kpcFt710 && F7.on && !fresh) return { cls: 'warn', line: '⏳ Starting the FT-710 scope reader… (radio menu SCU-LAN10 = ON; close other scope programs)' };
    if (fresh && r.src === 'sim') return { cls: 'ok', line: '🧪 Pretend RF scope (no radio): carriers at the spots · ◇ = a spot from the internet' };
    if (fresh && r.src === 'af') return { cls: 'af', line: '🔊 AUDIO picture (0–' + (S.afHi || 3000) + ' Hz) from the radio\'s USB sound: only what is inside the radio\'s filter, not the band' };
    if (cat && G.KPCCat.get().proto === 'icom' && CIV_SCOPE[id] && G.KPCCat.link() !== 'serial') return { cls: 'warn', line: 'The scope needs the USB cable link (not rigctld / flrig).' };
    if (cat && G.KPCCat.get().proto === 'icom' && CIV_SCOPE[id]) return { cls: 'warn', line: civOn ? '⏳ Asked the radio for its scope… no data yet. On the radio: SET › Connectors › CI-V › CI-V USB Port = Unlink from [REMOTE], CI-V USB Baud Rate = 115200.' : '⏳ starting the radio\'s scope…' };
    return { cls: 'warn', line: AP.running() ? '⏳ Waiting for sound…' : 'This radio sends no scope over its cable: press START (STATION → Sound) for the AUDIO picture.' };
  }

  /* ---------------- the RADIO screen card ---------------- */
  function card() {
    const on = $('rdOn'); if (!on) return; let c = $('rdScope');
    if (!c) { const grid = on.querySelector('.rdgrid'); if (!grid) return; grid.insertAdjacentHTML('beforebegin', '<div class="card rdscope" id="rdScope"><h2>🌊 Scope <span class="cxsub" id="scSrc"></span></h2><canvas id="scCv" class="sccv"></canvas><div class="chips" id="scChips"></div><p class="hint" id="scSt"></p></div>'); c = $('rdScope'); }
    const f7 = f7Radio() && !!G.kpcFt710, f7s = [20, 50, 100, 200, 500];
    const civ = hasCiv(), spans = [[2500, '±2.5k'], [5000, '±5k'], [10000, '±10k'], [25000, '±25k'], [50000, '±50k'], [100000, '±100k']];
    $('scChips').innerHTML = `<button type="button" class="chip${S.on ? ' on' : ''}" id="scOn">${S.on ? 'ON' : 'OFF'}</button>` +
      (civ || simOn() ? spans.map(([v, t]) => `<button type="button" class="chip${S.civSpan === v ? ' on' : ''}" data-scs="${v}">${t}</button>`).join('') + (civ ? '<button type="button" class="chip" id="scFix">FIXED</button>' : '') : '') +
      (f7 ? '<span class="kv"><i>RADIO SPAN</i></span>' + f7s.map(v => `<button type="button" class="chip${(+S.f7Span || 100) === v ? ' on' : ''}" data-f7s="${v}" title="Set the same SPAN on the FT-710">${v}k</button>`).join('') : '') +
      `<button type="button" class="chip" data-scc="-1">dim</button><button type="button" class="chip" data-scc="1">bright</button>` +
      `<span class="kv scshow"><i>SHOW</i></span>` + [['spots', '◇ TAGS'], ['calls', 'CALLS'], ['park', '🌲 PARK #'], ['sota', '▲ SOTA'], ['rbn', 'SKIMMERS'], ['plan', 'BAND PLAN'], ['pass', 'MY FILTER'], ['grid', 'GRID'], ['peak', 'PEAK']]
        .map(([k, t]) => `<button type="button" class="chip${S.show[k] ? ' on' : ''}" data-scw="${k}" aria-pressed="${!!S.show[k]}">${t}</button>`).join('') +
      `<button type="button" class="chip" id="scFull" title="The scope on the whole screen (Esc to come back)">⛶</button>`;
    $('scOn').onclick = async () => { S.on = !S.on; save(); if (!S.on) await civStop(); card(); };
    c.querySelectorAll('[data-scs]').forEach(b => { b.onclick = async () => { await civSpan(+b.dataset.scs); card(); }; });
    if ($('scFix')) $('scFix').onclick = () => civFixed();
    c.querySelectorAll('[data-f7s]').forEach(b => { b.onclick = () => { S.f7Span = +b.dataset.f7s; save(); card(); }; });
    c.querySelectorAll('[data-scw]').forEach(b => { b.onclick = () => { const k = b.dataset.scw; S.show[k] = S.show[k] ? 0 : 1; save(); b.classList.toggle('on', !!S.show[k]); b.setAttribute('aria-pressed', !!S.show[k]); }; });
    if ($('scFull')) $('scFull').onclick = () => { const el = $('rdScope'); if (document.fullscreenElement) document.exitFullscreen(); else if (el.requestFullscreen) el.requestFullscreen().catch(() => el.classList.toggle('scbig')); else el.classList.toggle('scbig'); };
    c.querySelectorAll('[data-scc]').forEach(b => { b.onclick = () => { S.contrast = Math.max(0.5, Math.min(3, (S.contrast || 1) * (b.dataset.scc === '1' ? 1.25 : 0.8))); save(); }; });
    mount($('scCv')); stat();
  }
  function stat() { const s = status(); if ($('scSt')) { $('scSt').textContent = s.line; $('scSt').className = 'hint sc-' + s.cls; } if ($('scSrc')) { const r = ROWS[ROWS.length - 1]; $('scSrc').textContent = !r ? '' : r.src === 'af' ? 'AUDIO (Hz)' : r.src === 'sim' ? 'RF · pretend' : 'RF · from the radio'; } }
  setInterval(() => { if (document.body.dataset.screen === 'radio') { if (!$('rdScope')) card(); stat(); } }, 1000);
  AP.on('screen', n => { if (n === 'radio') setTimeout(card, 50); });

  G.KPCScope = { tags: () => (W1 && W1.tags) || 0, hits: () => (W1 ? W1.hits.slice() : []), setTune: f => { TUNE_HOOK = f; }, _f7Row: f7Row, f7: () => Object.assign({}, F7), on: f => { subs.add(f); return () => subs.delete(f); }, S, tap, push, rows: () => ROWS, slow: () => SLOW, status, state: () => Object.assign({}, ST), underlay, mount, card, civFrame, hasCiv, civStart, civStop, civSpan, afBlock, simTick, _civBytes: civBytes, CIV_SCOPE };
})(window);
