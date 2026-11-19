/* KPC digital modes engine: RTTY, SSTV and Feld Hellschreiber (Oct 17; Nov 18: PSK31 + WSPR moved out, see below) (Brandon Oct 17 2026: 'go ahead with RTTY, PSK31, SSTV, WSPR').
   Pure sound math at 12 000 samples a second, shared by the KPC Logger and both Hunters Lounges (kpc-logger-ft8.js draws the screens).
   - RTTY: 45.45 / 50 / 75 baud, any shift; two matched filters + W7AY-style automatic threshold; Baudot (US figures, unshift on space).
   - PSK31 and WSPR are NOT in the app any more (Nov 18 2026): their code came from GPL programs (fldigi's Varicode table, a port of
     WSJT-X wsprd). Both wait in extras/gpl-hold/ for the separate extras app (or a clean-room rewrite).
   - SSTV: receive Martin 1/2, Scottie 1/2/DX, Robot 36/72, PD 50/90/120/160/180/240/290 (VIS code picks the mode, line sync fixes slant);
     send Martin 1, Scottie 1, Robot 36, PD 120.
   */
(function (G) {
  'use strict';
  const R = 12000, TAU = Math.PI * 2;
  const D = {};

  /* ---------- helpers ---------- */
  function lp(fc, fs) { const w = TAU * fc / fs, c = Math.cos(w), s = Math.sin(w), a = s / Math.SQRT2, a0 = 1 + a;
    return { b0: (1 - c) / 2 / a0, b1: (1 - c) / a0, b2: (1 - c) / 2 / a0, a1: -2 * c / a0, a2: (1 - a) / a0 }; }
  function BQ(c) { this.c = c; this.x1 = this.x2 = this.y1 = this.y2 = 0; }
  BQ.prototype.run = function (x) { const c = this.c, y = c.b0 * x + c.b1 * this.x1 + c.b2 * this.x2 - c.a1 * this.y1 - c.a2 * this.y2; this.x2 = this.x1; this.x1 = x; this.y2 = this.y1; this.y1 = y; return y; };
  function fft(re, im, inv) { const n = re.length; for (let i = 1, j = 0; i < n; i++) { let b = n >> 1; for (; j & b; b >>= 1) j ^= b; j ^= b; if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; } }
    for (let len = 2; len <= n; len <<= 1) { const a = (inv ? 1 : -1) * TAU / len, wr = Math.cos(a), wi = Math.sin(a);
      for (let i = 0; i < n; i += len) { let cr = 1, ci = 0; for (let k = 0; k < len / 2; k++) { const u = i + k, v = u + len / 2, xr = re[v] * cr - im[v] * ci, xi = re[v] * ci + im[v] * cr;
        re[v] = re[u] - xr; im[v] = im[u] - xi; re[u] += xr; im[u] += xi; const t = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = t; } } } }
  D.fft = fft;
  /* a tone of changing frequency, phase kept smooth: segs = [[Hz, seconds], …] (amplitude 0 = silence) */
  function tones(segs, rate, amp) { let tot = 0; for (const s of segs) tot += s[1]; const out = new Float32Array(Math.ceil(tot * rate) + 8); let n = 0, ph = 0, acc = 0;
    for (const [f, d, a] of segs) { acc += d * rate; const end = Math.floor(acc), w = TAU * f / rate, A = a == null ? (amp || 1) : a; for (; n < end; n++) { out[n] = A * Math.sin(ph); ph += w; if (ph > TAU) ph -= TAU; } }
    return out.subarray(0, n); }
  D.tones = tones;

  /* ======================= RTTY ======================= */
  const LTR = ['', 'E', '\n', 'A', ' ', 'S', 'I', 'U', '\r', 'D', 'R', 'J', 'N', 'F', 'C', 'K', 'T', 'Z', 'L', 'W', 'H', 'Y', 'P', 'Q', 'O', 'B', 'G', '', 'M', 'X', 'V', ''];
  const FIG = ['', '3', '\n', '-', ' ', '\x07', '8', '7', '\r', '$', '4', "'", ',', '!', ':', '(', '5', '"', ')', '2', '#', '6', '0', '1', '9', '?', '&', '', '.', '/', ';', ''];
  const FIGS = 27, LTRS = 31;
  function RttyRx(o) { this.set(o || {}); this.onChar = null; }
  RttyRx.prototype.set = function (o) {
    this.center = o.center || this.center || 1500; this.shift = o.shift || this.shift || 170; this.baud = o.baud || this.baud || 45.45; this.rev = o.rev != null ? !!o.rev : !!this.rev;
    const fm = this.center + (this.rev ? -1 : 1) * this.shift / 2, fs = this.center - (this.rev ? -1 : 1) * this.shift / 2;
    this.wm = TAU * fm / R; this.ws = TAU * fs / R; this.pm = this.ps = 0; this.N = Math.round(R / this.baud);
    this.buf = new Float32Array(this.N * 4); this.bp = 0; this.sum = [0, 0, 0, 0];
    this.mE = this.sE = 1e-3; this.mN = this.sN = 0; this.prev = 1; this.st = 0; this.cnt = 0; this.bits = 0; this.figs = false; this.q = 0; this.lvm = 0; this.lvs = 0;
  };
  RttyRx.prototype.tune = function (center) { /* move without losing the character in progress (AFC, taps) */
    this.center = center; const fm = center + (this.rev ? -1 : 1) * this.shift / 2, fs = center - (this.rev ? -1 : 1) * this.shift / 2; this.wm = TAU * fm / R; this.ws = TAU * fs / R; };
  RttyRx.prototype.feed = function (x) {
    const N = this.N, b = this.buf, p = this.bp * 4, s = this.sum;
    this.pm += this.wm; if (this.pm > TAU) this.pm -= TAU; this.ps += this.ws; if (this.ps > TAU) this.ps -= TAU;
    const v0 = x * Math.cos(this.pm), v1 = x * Math.sin(this.pm), v2 = x * Math.cos(this.ps), v3 = x * Math.sin(this.ps);
    s[0] += v0 - b[p]; s[1] += v1 - b[p + 1]; s[2] += v2 - b[p + 2]; s[3] += v3 - b[p + 3]; b[p] = v0; b[p + 1] = v1; b[p + 2] = v2; b[p + 3] = v3; this.bp = (this.bp + 1) % N;
    const M = Math.hypot(s[0], s[1]) / N, Sp = Math.hypot(s[2], s[3]) / N;
    const fa = 4 / N, sl = 1 / (N * 24);
    this.mE += (M - this.mE) * (M > this.mE ? fa : sl); this.sE += (Sp - this.sE) * (Sp > this.sE ? fa : sl);
    this.mN += (M - this.mN) * (M < this.mN ? fa : sl); this.sN += (Sp - this.sN) * (Sp < this.sN ? fa : sl);
    const mc = Math.min(M, this.mE), sc = Math.min(Sp, this.sE);
    const v = (mc - this.mN) * (this.mE - this.mN) - (sc - this.sN) * (this.sE - this.sN) - 0.5 * ((this.mE - this.mN) ** 2 - (this.sE - this.sN) ** 2);
    const bit = v > 0 ? 1 : 0; this.lvm = M; this.lvs = Sp;
    if (this.st === 0) { if (this.prev === 1 && bit === 0) { this.st = 1; this.cnt = 0; } }
    else { this.cnt++; const half = N >> 1;
      if (this.cnt === half) { if (bit !== 0) this.st = 0; else this.bits = 0; }
      else if (this.cnt > half && (this.cnt - half) % N === 0) { const k = (this.cnt - half) / N;
        if (k <= 5) this.bits |= bit << (k - 1);
        else { this.st = 0; const ok = bit === 1; this.q += ((ok ? 1 : 0) - this.q) * 0.18; if (ok) this.code(this.bits); } } }
    this.prev = bit;
  };
  RttyRx.prototype.code = function (c) {
    if (c === LTRS) { this.figs = false; return; } if (c === FIGS) { this.figs = true; return; }
    const ch = (this.figs ? FIG : LTR)[c]; if (c === 4) this.figs = false; /* unshift on space */
    if (ch && this.onChar) this.onChar(ch === '\r' ? '' : ch === '\x07' ? '' : ch);
  };
  RttyRx.prototype.level = function () { return { m: this.lvm, s: this.lvs, q: this.q, sig: Math.max(this.mE, this.sE) / Math.max(1e-9, Math.max(this.mN, this.sN) + 1e-6) }; };
  D.RttyRx = RttyRx;
  const R_L = {}, R_F = {}; LTR.forEach((c, i) => { if (c && c !== ' ') R_L[c] = i; }); FIG.forEach((c, i) => { if (c && c !== ' ') R_F[c] = i; });
  /* text → audio (AFSK). Starts with a short mark tone and LTRS so receivers lock on. */
  D.rttyTx = function (text, o, rate) {
    o = o || {}; const center = o.center || 1500, shift = o.shift || 170, baud = o.baud || 45.45, rev = !!o.rev, fm = center + (rev ? -1 : 1) * shift / 2, fs = center - (rev ? -1 : 1) * shift / 2, T = 1 / baud;
    const segs = [[fm, 0.3]]; const send = c => { segs.push([fs, T]); for (let i = 0; i < 5; i++) segs.push([(c >> i) & 1 ? fm : fs, T]); segs.push([fm, 1.5 * T]); };
    send(LTRS); send(LTRS); let figs = false;
    for (let ch of String(text).toUpperCase().replace(/\r/g, '')) {
      if (ch === '\n') { send(8); send(2); continue; }
      if (ch === ' ') { send(4); figs = false; continue; }
      if (R_L[ch] != null) { if (figs) { send(LTRS); figs = false; } send(R_L[ch]); }
      else if (R_F[ch] != null) { if (!figs) { send(FIGS); figs = true; } send(R_F[ch]); }
    }
    send(LTRS); segs.push([fm, 0.15]);
    return tones(segs, rate || R, 1);
  };

  /* PSK31: taken out of the app Nov 18 2026 (Brandon: 'hide the ones with license issues we move later'): its Varicode table came
     from fldigi (GPL). Kept in extras/gpl-hold/kpc-dsp-full-GPL.js for the extras app / a clean-room rewrite from the PSK31 spec. */

  /* ======================= SSTV ======================= */
  const PD = (vis, w, h, px) => ({ vis, w, h, rows: 2, yuv: 'pd', pre: 0, syncAt: 0, segs: [['s', 20], ['g', 2.08], ['Y0', w * px], ['V', w * px], ['U', w * px], ['Y1', w * px]] });
  const MART = (vis, sc) => ({ vis, w: 320, h: 256, rows: 1, pre: 0, syncAt: 0, segs: [['s', 4.862], ['g', .572], ['G', sc], ['g', .572], ['B', sc], ['g', .572], ['R', sc], ['g', .572]] });
  const SCOT = (vis, sc) => ({ vis, w: 320, h: 256, rows: 1, pre: 9, syncAt: 1.5 + sc + 1.5 + sc, segs: [['g', 1.5], ['G', sc], ['g', 1.5], ['B', sc], ['s', 9], ['g', 1.5], ['R', sc]] });
  const SSTV = {
    'Martin 1': MART(44, 146.432), 'Martin 2': MART(40, 73.216),
    'Scottie 1': SCOT(60, 138.24), 'Scottie 2': SCOT(56, 88.064), 'Scottie DX': SCOT(76, 345.6),
    'Robot 36': { vis: 8, w: 320, h: 240, rows: 1, yuv: 'r36', pre: 0, syncAt: 0, segs: [['s', 9], ['g', 3], ['Y', 88], ['g', 4.5], ['g', 1.5], ['C', 44]] },
    'Robot 72': { vis: 12, w: 320, h: 240, rows: 1, yuv: 'r72', pre: 0, syncAt: 0, segs: [['s', 9], ['g', 3], ['Y', 138], ['g', 4.5], ['g', 1.5], ['V', 69], ['g', 4.5], ['g', 1.5], ['U', 69]] },
    'PD 50': PD(93, 320, 256, .286), 'PD 90': PD(99, 320, 256, .532), 'PD 120': PD(95, 640, 496, .19), 'PD 160': PD(98, 512, 400, .382),
    'PD 180': PD(96, 640, 496, .286), 'PD 240': PD(97, 640, 496, .382), 'PD 290': PD(94, 800, 616, .286)
  };
  for (const k in SSTV) { const m = SSTV[k]; m.name = k; m.L = m.segs.reduce((a, s) => a + s[1], 0); m.lines = m.h / m.rows; m.secs = (m.pre + m.L * m.lines) / 1000; }
  const BYVIS = {}; for (const k in SSTV) BYVIS[SSTV[k].vis] = SSTV[k];
  D.SSTV = SSTV;
  const clamp = v => v < 0 ? 0 : v > 255 ? 255 : v;
  function yuv2rgb(Y, U, V, o, i) { o[i] = clamp(Y + 1.402 * (V - 128)); o[i + 1] = clamp(Y - 0.344136 * (U - 128) - 0.714136 * (V - 128)); o[i + 2] = clamp(Y + 1.772 * (U - 128)); o[i + 3] = 255; }
  /* receiver: feed() every 12 kHz sample. Calls onStart(mode), onRow(y, rgba Uint8ClampedArray width*4), onEnd(mode, rowsDone) */
  function SstvRx() { const c = lp(900, R); this.f = [new BQ(c), new BQ(c), new BQ(c), new BQ(c)]; this.ph = 0; this.pr = 1; this.pi = 0; this.ms = new Float32Array(1200); this.mi = 0; this.msAcc = 0; this.msN = 0;
    this.n = 0; this.img = null; this.onStart = this.onRow = this.onEnd = null; this.cand = null; this.auto = true; this.fl = 1900;
    const T = this.T = { r: new Float64Array(6), i: new Float64Array(6), c: new Float64Array(6).fill(1), s: new Float64Array(6), wc: new Float64Array(6), ws: new Float64Array(6), n: 0, zr: new Float64Array(1200 * 12) }; VT.forEach((f, k) => { T.wc[k] = Math.cos(TAU * f / R); T.ws[k] = Math.sin(TAU * f / R); }); }
  SstvRx.prototype.feed = function (x) {
    this.ph += TAU * 1900 / R; if (this.ph > TAU) this.ph -= TAU;
    const i = this.f[1].run(this.f[0].run(x * Math.cos(this.ph))), q = this.f[3].run(this.f[2].run(-x * Math.sin(this.ph)));
    const dr = i * this.pr + q * this.pi, di = q * this.pr - i * this.pi; this.pr = i; this.pi = q;
    let f = 1900 + Math.atan2(di, dr) * R / TAU; if (!(f > 900 && f < 2700)) f = f > 2700 ? 2700 : 900; this.fl += (f - this.fl) * 0.5; f = this.fl;
    this.n++;
    if (this.img) this.imgIn(f);
    this.toneIn(x);
    this.msAcc += f; if (++this.msN === 12) { this.ms[this.mi % 1200] = this.msAcc / 12; this.mi++; this.msAcc = 0; this.msN = 0; if (!this.img && this.auto) this.visCheck(); }
    this.freq = f;
  };
  /* VIS code by tone energy (matched to each 30 ms bit), which holds up in noise far better than reading the frequency */
  const VT = [1100, 1200, 1300, 1900, 1500, 2300];
  SstvRx.prototype.toneIn = function (x) { const T = this.T; for (let k = 0; k < 6; k++) { const c = T.c[k], sn = T.s[k]; T.r[k] += x * c; T.i[k] -= x * sn; const nc = c * T.wc[k] - sn * T.ws[k]; T.s[k] = c * T.ws[k] + sn * T.wc[k]; T.c[k] = nc; }
    if (++T.n === 12) { T.n = 0; const j = (this.mi % 1200) * 12; for (let k = 0; k < 6; k++) { T.zr[j + k * 2] = T.r[k]; T.zr[j + k * 2 + 1] = T.i[k]; T.r[k] = T.i[k] = 0; const g = 1 / Math.hypot(T.c[k], T.s[k]); T.c[k] *= g; T.s[k] *= g; } } };
  SstvRx.prototype.E = function (k, a, b, ch) { /* energy of tone k from a to b ms ago (coherent over chunks of ch ms) */ const T = this.T; let tot = 0, r = 0, i = 0, n = 0;
    for (let m = b; m > a; m--) { const j = (((this.mi - m) % 1200 + 1200) % 1200) * 12; r += T.zr[j + k * 2]; i += T.zr[j + k * 2 + 1]; if (++n === ch) { tot += r * r + i * i; r = i = 0; n = 0; } } return tot + r * r + i * i; };
  SstvRx.prototype.visCheck = function () {
    if (this.cand && this.n - this.cand.at > 12 * 15) { const c = this.cand; this.cand = null; this.start(BYVIS[c.code], c.at); return; }
    if (this.mi < 1000) return;
    const on = (a, b, k, others) => { const e = this.E(k, a, b, b - a); let o = 0; for (const q of others) o = Math.max(o, this.E(q, a, b, b - a)); return e / (o + 1e-12); };
    const rs = on(3, 27, 1, [0, 2, 3]); if (rs < 2.5) return; const ra = on(273, 297, 1, [0, 2, 3]); if (ra < 2.5) return;
    const lead = this.E(3, 330, 570, 10), oth = Math.max(this.E(4, 330, 570, 10), this.E(1, 330, 570, 10), this.E(5, 330, 570, 10)); if (lead < 3 * oth) return;
    let code = 0, ones = 0, sc = Math.log(rs) + Math.log(ra);
    for (let b = 0; b < 8; b++) { const lo = 270 - 30 * b - 27, hi = 270 - 30 * b - 3, e1 = this.E(0, lo, hi, 24), e0 = this.E(2, lo, hi, 24); const one = e1 > e0, r = (one ? e1 / (e0 + 1e-12) : e0 / (e1 + 1e-12)); if (r < 1.8) return; sc += Math.log(r); if (one) { ones++; if (b < 7) code |= 1 << b; } }
    if (ones % 2 !== 0 || !BYVIS[code]) return;
    if (!this.cand || this.cand.code !== code && sc > this.cand.sc) this.cand = { code, sc, at: this.n, first: this.n, last: this.n };
    else if (this.cand.code === code) { if (sc > this.cand.sc * 0.92) { this.cand.last = this.n; this.cand.at = Math.round((this.cand.first + this.cand.last) / 2); } if (sc > this.cand.sc) this.cand.sc = sc; }
  };
  /* start an image: mode + the sample number where line 0 begins (after VIS, or now for a manual start) */
  SstvRx.prototype.start = function (m, at, manual) {
    const len = Math.ceil((m.pre + m.L * (m.lines + 1)) / 1000 * R * 1.1) + R;
    this.img = { m, t0: at - 12 * 0 + (manual ? 0 : 0), F: new Float32Array(len), P: new Float64Array(len + 1), S: new Float64Array(len + 1), n: 0, base: at, line: 0, fit: [], miss: 0, jump: 0, manual: !!manual, chroma: null, rowbuf: null };
    const im = this.img; /* samples already past `at` (the 15 ms wait) are re-made from the freq history is not possible, so fill them with 1500 */
    const late = Math.max(0, this.n - at); for (let k = 0; k < late; k++) this.imgIn(1500, true);
    if (this.onStart) this.onStart(m);
    void im;
  };
  SstvRx.prototype.stop = function () { if (this.img) { const im = this.img; this.img = null; if (this.onEnd) this.onEnd(im.m, im.line * im.m.rows); } };
  SstvRx.prototype.imgIn = function (f) {
    const im = this.img; if (im.n >= im.F.length) { this.stop(); return; }
    const k = im.n; im.F[k] = f; im.P[k + 1] = im.P[k] + f; im.S[k + 1] = im.S[k] + (f < 1350 ? 1 : 0); im.n++;
    const m = im.m, sps = R / 1000;
    /* is the next line complete? */
    const pred = this.lineStart(im.line), end = pred + m.L * sps + 8 * sps;
    if (im.n >= end) this.doLine();
  };
  SstvRx.prototype.lineStart = function (n) { const im = this.img, m = im.m, sps = R / 1000; const f = im.fit;
    if (f.length >= 4) { let sx = 0, sy = 0, sxx = 0, sxy = 0; for (const [x, y] of f) { sx += x; sy += y; sxx += x * x; sxy += x * y; } const N = f.length, d = N * sxx - sx * sx; if (d) { const b = (N * sxy - sx * sy) / d, a = (sy - b * sx) / N; if (b > m.L * sps * 0.98 && b < m.L * sps * 1.02) return a + b * n; } }
    if (f.length) { const [x, y] = f[f.length - 1]; return y + (n - x) * m.L * sps; }
    return m.pre * sps + n * m.L * sps; };
  SstvRx.prototype.doLine = function () {
    const im = this.img, m = im.m, sps = R / 1000, n = im.line; let st = this.lineStart(n);
    /* find the sync pulse near where it should be */
    const sl = Math.round(m.segs.find(s => s[0] === 's')[1] * sps), exp = st + m.syncAt * sps, win = Math.round((im.fit.length >= 4 ? 2.5 : im.manual && n < 2 ? m.L / 2 : 14) * sps);
    let bp = -1, bs = 0; for (let p = Math.max(0, Math.round(exp - win)); p <= Math.round(exp + win) && p + sl <= im.n; p++) { const s = (im.S[p + sl] - im.S[p]) / sl; if (s > bs + 1e-9) { bs = s; bp = p; } }
    if (bs > 0.62 && bp >= 0) { const got = bp - m.syncAt * sps, d = got - st;
      if (!im.fit.length || Math.abs(d) < (im.fit.length < 4 ? 14 : 6) * sps || im.manual && im.fit.length < 2) {
        /* a jump (the sound card dropped or doubled a few samples): follow the sync pulse and start the line fit again */
        if (im.fit.length >= 4 && Math.abs(d) > 1.2 * sps) { if (++im.jump >= 2) { im.fit = im.fit.slice(-1); im.jump = 0; } st = got; } else im.jump = 0;
        im.fit.push([n, got]); if (im.fit.length > 40) im.fit.shift(); if (im.fit.length < 4) st = got; } im.miss = 0; } else im.miss++;
    this.drawLine(n, st); im.line++;
    if (im.line >= m.lines || im.miss > 24) this.stop();
  };
  SstvRx.prototype.chan = function (a, dur, W) { const im = this.img, out = new Float32Array(W), step = dur / W;
    for (let x = 0; x < W; x++) { let lo = Math.round(a + x * step), hi = Math.round(a + (x + 1) * step); if (hi <= lo) hi = lo + 1; lo = Math.max(0, Math.min(im.n - 1, lo)); hi = Math.max(lo + 1, Math.min(im.n, hi)); const f = (im.P[hi] - im.P[lo]) / (hi - lo); out[x] = clamp((f - 1500) / 800 * 255); } return out; };
  SstvRx.prototype.drawLine = function (n, st) {
    const im = this.img, m = im.m, sps = R / 1000, W = m.w; let t = st; const C = {};
    for (const [k, ms] of m.segs) { const d = ms * sps; if (k.length <= 2 && k !== 's' && k !== 'g') C[k] = this.chan(t, d, W); t += d; }
    const row = () => new Uint8ClampedArray(W * 4);
    if (!m.yuv) { const o = row(); for (let x = 0; x < W; x++) { o[x * 4] = C.R[x]; o[x * 4 + 1] = C.G[x]; o[x * 4 + 2] = C.B[x]; o[x * 4 + 3] = 255; } if (this.onRow) this.onRow(n, o); return; }
    if (m.yuv === 'pd') { const a = row(), b = row(); for (let x = 0; x < W; x++) { yuv2rgb(C.Y0[x], C.U[x], C.V[x], a, x * 4); yuv2rgb(C.Y1[x], C.U[x], C.V[x], b, x * 4); } if (this.onRow) { this.onRow(2 * n, a); this.onRow(2 * n + 1, b); } return; }
    if (m.yuv === 'r72') { const o = row(); for (let x = 0; x < W; x++) yuv2rgb(C.Y[x], C.U[x], C.V[x], o, x * 4); if (this.onRow) this.onRow(n, o); return; }
    /* Robot 36: even lines carry R-Y, odd lines B-Y; each pair shares both */
    if (n % 2 === 0) { im.chroma = { Y: C.Y, V: C.C, n }; const o = row(); for (let x = 0; x < W; x++) yuv2rgb(C.Y[x], 128, C.C[x], o, x * 4); if (this.onRow) this.onRow(n, o); }
    else { const p = im.chroma && im.chroma.n === n - 1 ? im.chroma : { Y: C.Y, V: new Float32Array(W).fill(128) }; const a = row(), b = row();
      for (let x = 0; x < W; x++) { yuv2rgb(p.Y[x], C.C[x], p.V[x], a, x * 4); yuv2rgb(C.Y[x], C.C[x], p.V[x], b, x * 4); } if (this.onRow) { this.onRow(n - 1, a); this.onRow(n, b); } }
  };
  SstvRx.prototype.manual = function (name) { const m = SSTV[name]; if (m) this.start(m, this.n, true); };
  D.SstvRx = SstvRx;
  /* image (ImageData-like {width,height,data} already sized to the mode) → audio */
  D.sstvTx = function (img, name, rate) {
    const m = SSTV[name]; if (!m) return null; const W = m.w, px = img.data, fr = v => 1500 + 800 * v / 255;
    const segs = [[1900, .3], [1200, .01], [1900, .3], [1200, .03]]; let ones = 0; for (let b = 0; b < 7; b++) { const one = (m.vis >> b) & 1; ones += one; segs.push([one ? 1100 : 1300, .03]); } segs.push([ones % 2 ? 1100 : 1300, .03]); segs.push([1200, .03]);
    if (m.pre) segs.push([1200, m.pre / 1000]);
    const P = (x, y) => { const i = (y * W + x) * 4; return [px[i], px[i + 1], px[i + 2]]; };
    const Yv = p => .299 * p[0] + .587 * p[1] + .114 * p[2], Uv = p => 128 - .168736 * p[0] - .331264 * p[1] + .5 * p[2], Vv = p => 128 + .5 * p[0] - .418688 * p[1] - .081312 * p[2];
    for (let n = 0; n < m.lines; n++) {
      for (const [k, ms] of m.segs) { const d = ms / 1000;
        if (k === 's') { segs.push([1200, d]); continue; }
        if (k === 'g') { segs.push([m.yuv === 'r36' && ms === 4.5 ? (n % 2 ? 2300 : 1500) : m.yuv && ms === 1.5 ? 1900 : 1500, d]); continue; }
        const y0 = m.rows === 2 ? 2 * n : n, y1 = m.rows === 2 ? 2 * n + 1 : n, pd = d / W;
        for (let x = 0; x < W; x++) { let v;
          if (k === 'R' || k === 'G' || k === 'B') v = P(x, y0)['RGB'.indexOf(k)];
          else if (k === 'Y' || k === 'Y0') v = Yv(P(x, y0)); else if (k === 'Y1') v = Yv(P(x, y1));
          else if (k === 'U' || k === 'V' || k === 'C') { const kk = k === 'C' ? (n % 2 ? 'U' : 'V') : k; const f = kk === 'U' ? Uv : Vv; v = m.rows === 2 ? (f(P(x, y0)) + f(P(x, y1))) / 2 : (m.yuv === 'r36' ? (f(P(x, n)) + f(P(x, Math.min(m.h - 1, n % 2 ? n - 1 : n + 1)))) / 2 : f(P(x, n))); }
          segs.push([fr(v), pd]); } } }
    return tones(segs, rate || R, 1);
  };

  /* WSPR: taken out of the app Nov 18 2026 (same reason): the decoder was a port of WSJT-X wsprd (GPL v3). Kept in
     extras/gpl-hold/kpc-dsp-full-GPL.js for the extras app. */

  /* ---------------- Feld Hellschreiber (Oct 17, Brandon: 'hellschreiber') ----------------
     On/off keyed tone, 2.5 characters a second: each character = 7 columns, each column = 14 picture elements scanned
     bottom to top (245 elements a second, about 4.08 ms each). Nothing to decode: the receiver just paints the tone's
     strength as a picture, so your eyes read it (that's why it copies through noise and needs no sync). */
  const HELLF = {
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'], 'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'], 'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'], 'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
    'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01111'], 'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'], 'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
    'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'], 'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'], 'N': ['10001', '10001', '11001', '10101', '10011', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'], 'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'], 'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'], 'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'], 'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'], 'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'], 'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'], '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'], '3': ['11111', '00010', '00100', '00010', '00001', '10001', '01110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'], '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
    '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'], '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'], '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
    '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'], ',': ['00000', '00000', '00000', '00000', '01100', '00100', '01000'],
    '?': ['01110', '10001', '00001', '00010', '00100', '00000', '00100'], '/': ['00000', '00001', '00010', '00100', '01000', '10000', '00000'],
    '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'], '=': ['00000', '00000', '11111', '00000', '11111', '00000', '00000'],
    '+': ['00000', '00100', '00100', '11111', '00100', '00100', '00000'], ':': ['00000', '01100', '01100', '00000', '01100', '01100', '00000'],
    "'": ['01100', '00100', '01000', '00000', '00000', '00000', '00000'], '(': ['00010', '00100', '01000', '01000', '01000', '00100', '00010'],
    ')': ['01000', '00100', '00010', '00010', '00010', '00100', '01000'], '!': ['00100', '00100', '00100', '00100', '00100', '00000', '00100'],
    '@': ['01110', '10001', '10111', '10101', '10111', '10000', '01110'], '#': ['01010', '01010', '11111', '01010', '11111', '01010', '01010'],
    ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000']
  };
  D.HELL = { cps: 2.5, cols: 7, rows: 14, rate: 245 };
  /* columns of 14 elements (bottom first) for a text */
  function hellCols(text) { const out = []; for (const ch of String(text).toUpperCase()) { const g = HELLF[ch] || HELLF[ch === '\n' ? ' ' : '?'];
      const C = [[], [], [], [], [], [], []]; for (let c = 0; c < 7; c++) for (let r = 13; r >= 0; r--) { const row = Math.floor(r / 2), on = c >= 1 && c <= 5 && g[row][c - 1] === '1'; C[c].push(on ? 1 : 0); }
      /* rows are listed top to bottom; the scan goes bottom to top, so element 0 = bottom (row 6) */
      out.push(...C); } return out; }
  D.hellTx = function (text, fc, rate) { rate = rate || R; const cols = hellCols(' ' + text + ' '), el = rate / 245, N = Math.ceil(cols.length * 14 * el), out = new Float32Array(N + 8);
    const rise = Math.max(4, Math.round(rate * 0.0012)); let ph = 0; const w = TAU * fc / rate;
    const bits = []; for (const c of cols) for (const b of c) bits.push(b);
    for (let n = 0; n < N; n++) { const k = Math.floor(n / el), b = bits[k] || 0; let env = b; if (b) { const st = Math.round(k * el), en = Math.round((k + 1) * el); let a = Math.min(n - st, en - n) / rise;
        if (bits[k - 1]) a = Math.max(a, (en - n) / rise > 1 ? 1 : a); if (bits[k + 1]) a = Math.max(a, (n - st) / rise > 1 ? 1 : a); if (bits[k - 1] && bits[k + 1]) a = 1; env = Math.min(1, Math.max(0, a)); env = 0.5 - 0.5 * Math.cos(Math.PI * env); }
      out[n] = 0.85 * env * Math.sin(ph); ph += w; if (ph > TAU) ph -= TAU; } return out; };
  /* receiver: mix to 0 Hz, ~2 ms smoothing (passes 245 elements a second), strength per element, slow AGC */
  function HellRx(fc) { this.tune(fc || 1000); this.i = 0; this.q = 0; this.acc = 0; this.n = 0; this.pos = 0; this.pk = 1e-6; this.fl = 1e-7; this.onPx = null; this.sig = 0; }
  HellRx.prototype.tune = function (fc) { this.fc = fc; this.w = TAU * fc / R; this.ph = this.ph || 0; };
  HellRx.prototype.feed = function (x) {
    this.ph += this.w; if (this.ph > TAU) this.ph -= TAU; const a = 0.11;                    /* one-pole low-pass at ~220 Hz, run twice */
    this.i += a * (x * Math.cos(this.ph) - this.i); this.q += a * (-x * Math.sin(this.ph) - this.q);
    this.i2 = (this.i2 || 0) + a * (this.i - (this.i2 || 0)); this.q2 = (this.q2 || 0) + a * (this.q - (this.q2 || 0));
    this.acc += Math.sqrt(this.i2 * this.i2 + this.q2 * this.q2); this.n++; this.pos += 245 / R;
    if (this.pos >= 1) { this.pos -= 1; const v = this.acc / this.n; this.acc = 0; this.n = 0;
      this.pk = Math.max(v, this.pk * 0.9993); this.fl = Math.min(v, this.fl * 1.0005 + 1e-9); if (this.fl > v) this.fl = v;
      const span = Math.max(this.pk - this.fl, 1e-7), lvl = Math.max(0, Math.min(1, (v - this.fl) / span)); this.sig = this.sig * 0.995 + lvl * 0.005;
      if (this.onPx) this.onPx(lvl); } };
  D.HellRx = HellRx;
  D._hellCols = hellCols;

  G.KPCDsp = D;   /* app copy: named KPCDsp (the app's own KPCDigi is the FT8 screen) */
  if (typeof module !== 'undefined' && module.exports) module.exports = D;
})(typeof window !== 'undefined' ? window : typeof self !== 'undefined' ? self : globalThis);
