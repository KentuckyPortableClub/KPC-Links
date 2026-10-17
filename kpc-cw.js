/* KPC CW Practice — kpc-cw.html
   Hunt or activate a simulated POTA / SOTA station, run copy drills, or just practice sending.
   Everything runs in the browser: Web Audio for the tones, a keyer for paddles, an adaptive decoder
   for a straight key. Settings are saved on this device (localStorage "kpcCW").
   Nothing here is ever logged anywhere — these are practice contacts only. */
(function () {
'use strict';

/* ================================================================ Morse */
const MORSE = {
  A:'.-',B:'-...',C:'-.-.',D:'-..',E:'.',F:'..-.',G:'--.',H:'....',I:'..',J:'.---',K:'-.-',L:'.-..',M:'--',
  N:'-.',O:'---',P:'.--.',Q:'--.-',R:'.-.',S:'...',T:'-',U:'..-',V:'...-',W:'.--',X:'-..-',Y:'-.--',Z:'--..',
  0:'-----',1:'.----',2:'..---',3:'...--',4:'....-',5:'.....',6:'-....',7:'--...',8:'---..',9:'----.',
  '.':'.-.-.-',',':'--..--','?':'..--..','/':'-..-.','=':'-...-','+':'.-.-.','-':'-....-',"'":'.----.',
  '(':'-.--.',')':'-.--.-',':':'---...',';':'-.-.-.','"':'.-..-.','@':'.--.-.','!':'-.-.--'
};
const PROSIGN = { '<AR>':'.-.-.', '<SK>':'...-.-', '<KN>':'-.--.', '<BT>':'-...-', '<BK>':'-...-.-' };
const DECODE = {};
Object.keys(MORSE).forEach(k => { DECODE[MORSE[k]] = k; });
DECODE['...-.-'] = '<SK>'; DECODE['-...-.-'] = '<BK>'; DECODE['........'] = '<HH>';

/* split text into characters, keeping <XX> prosigns together; ' ' = word space */
function charsOf(text) {
  const out = []; const s = String(text).toUpperCase();
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '<') { const j = s.indexOf('>', i); if (j > i) { const p = s.slice(i, j + 1); if (PROSIGN[p]) { out.push(p); i = j; continue; } } }
    if (/\s/.test(c)) { if (out.length && out[out.length - 1] !== ' ') out.push(' '); continue; }
    if (MORSE[c]) out.push(c);
  }
  while (out.length && out[out.length - 1] === ' ') out.pop();
  return out;
}

/* Timeline of key-down marks [start,end] in seconds. Farnsworth spacing per the ARRL formula. */
function timeline(text, wpm, eff, jitter) {
  const u = 1.2 / wpm;
  let cg = 3 * u, wg = 7 * u;
  if (eff && eff < wpm) { const ta = (60 * wpm - 37.2 * eff) / (wpm * eff); cg = 3 * ta / 19; wg = 7 * ta / 19; }
  const j = jitter || 0, wob = () => 1 + (Math.random() - 0.5) * 2 * j;
  const marks = []; let t = 0;
  const cs = charsOf(text);
  cs.forEach((c, ci) => {
    if (c === ' ') { t += Math.max(0, wg - cg); return; }
    const code = PROSIGN[c] || MORSE[c];
    for (let i = 0; i < code.length; i++) {
      const d = (code[i] === '.' ? u : 3 * u) * wob();
      marks.push([t, t + d]); t += d;
      if (i < code.length - 1) t += u * wob();
    }
    if (ci < cs.length - 1) t += cg * wob();
  });
  return { marks, total: t };
}

/* ================================================================ Settings */
const DEF = {
  call: '', st: 'KY', ref: '', prog: 'pota',
  wpm: 18, eff: 18, pitch: 650, their: 600, vol: 0.7, noise: 0.12, qsb: true, fade: 2, pileN: 2,
  input: 'keyboard', iambic: 'B', swap: false, show: 'after', hints: true, pile: 2,
  over: 1.0, match: false, welcome: true, name: '', qth: '', nr: '', bandc: 'clean', spFmt: 'pota', spMin: 5, kochLevel: 2, drill: 'calls'
};
let S = Object.assign({}, DEF);
try { Object.assign(S, JSON.parse(localStorage.getItem('kpcCW') || '{}')); } catch (e) {}
// older saved settings: QSB on/off -> fading level, ACTIVITY 0-4 -> number of callers
try { const old = JSON.parse(localStorage.getItem('kpcCW') || '{}');
  if (!('fade' in old) && old.qsb === false) S.fade = 0;
  if (!('pileN' in old) && 'pile' in old) S.pileN = [0, 1, 2, 4, 6][old.pile] ?? 2;
  if (!('fade' in old) && old.over === 1.6) S.over = 1.0; // old default was slow to answer
} catch (e) {}
function save() { try { localStorage.setItem('kpcCW', JSON.stringify(S)); } catch (e) {} }

/* ================================================================ Audio */
let AC = null, master = null, myG = null, myOsc = null, noiseG = null, noiseF = null;
function audio() {
  if (!AC) {
    const C = window.AudioContext || window.webkitAudioContext;
    if (!C) return null;
    try { AC = new C({ latencyHint: 'interactive' }); } catch (e) { AC = new C(); }
    master = AC.createGain(); master.gain.value = S.vol; master.connect(AC.destination);
    myOsc = AC.createOscillator(); myOsc.type = 'sine'; myOsc.frequency.value = S.pitch;
    myG = AC.createGain(); myG.gain.value = 0;
    const myLvl = AC.createGain(); myLvl.gain.value = 0.55;
    myOsc.connect(myG); myG.connect(myLvl); myLvl.connect(master); myOsc.start();
    // band noise: white noise through a wide band-pass around the receive pitch
    const len = AC.sampleRate * 2, buf = AC.createBuffer(1, len, AC.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    const src = AC.createBufferSource(); src.buffer = buf; src.loop = true;
    noiseF = AC.createBiquadFilter(); noiseF.type = 'bandpass'; noiseF.frequency.value = S.their; noiseF.Q.value = 0.8;
    noiseG = AC.createGain(); noiseG.gain.value = 0;
    src.connect(noiseF); noiseF.connect(noiseG); noiseG.connect(master); src.start();
  }
  if (AC.state === 'suspended') AC.resume();
  return AC;
}
/* How long until sound reaches the speaker (ms). Bluetooth adds a lot that the page can't see. */
function latencyMs() { if (!AC) return null; return Math.round(((AC.baseLatency || 0) + (AC.outputLatency || 0)) * 1000); }
const RAMP = 0.0016; // ~5 ms rise/fall, no key clicks
function sidetone(on) {
  if (!audio()) return;
  const t = AC.currentTime;
  myG.gain.cancelScheduledValues(t);
  myG.gain.setTargetAtTime(on ? 1 : 0, t, RAMP);
}
function setNoise(on) {
  if (!AC) return;
  noiseG.gain.setTargetAtTime(on ? S.noise * 0.35 : 0, AC.currentTime, 0.15);
}
function applyAudio() {
  if (!AC) return;
  master.gain.setTargetAtTime(S.vol, AC.currentTime, 0.02);
  myOsc.frequency.setTargetAtTime(S.pitch, AC.currentTime, 0.01);
  noiseF.frequency.setTargetAtTime(S.their, AC.currentTime, 0.05);
  if (noiseG.gain.value > 0.0001 || running()) setNoise(true);
}

/* A simulated station: its own tone, level, fading and fist. */
const VOICES = new Set();
function Voice(o) {
  this.call = o.call; this.pitch = o.pitch; this.wpm = o.wpm; this.eff = o.eff || o.wpm;
  this.jit = o.jit || 0; this.level = o.level == null ? 0.8 : o.level; this.timer = null; this.done = null;
  if (!audio()) return;
  this.osc = AC.createOscillator(); this.osc.frequency.value = o.pitch;
  this.env = AC.createGain(); this.env.gain.value = 0;
  this.fade = AC.createGain(); this.fade.gain.value = this.level;
  this.osc.connect(this.env); this.env.connect(this.fade); this.fade.connect(master);
  // fading (QSB): a slow wobble on this station's level; depth and speed follow the FADING slider
  this.rate = Math.random(); this.lfo = AC.createOscillator(); this.depth = AC.createGain(); this.depth.gain.value = 0;
  this.lfo.connect(this.depth); this.depth.connect(this.fade.gain); this.lfo.start();
  this.noQsb = !!o.noQsb; this.fadeLvl = o.fade; this.bug = o.bug || 0; this.setQsb();
  this.osc.start(); VOICES.add(this);
}
// level 0 off, 1 light, 2 moderate, 3 deep, 4 deep & fast (fades almost to nothing)
const QSB = [[0, 0, 0], [0.25, 0.05, 0.12], [0.45, 0.07, 0.2], [0.7, 0.1, 0.3], [0.92, 0.25, 0.7]];
Voice.prototype.setQsb = function () {
  if (!AC || !this.lfo) return;
  const q = (this.fadeLvl != null ? QSB[this.fadeLvl] : this.noQsb ? QSB[0] : QSB[S.fade]) || QSB[0], f = q[0] * Math.min(1, 0.85 + this.rate * 0.3), t = AC.currentTime;
  const lo = Math.min(0.98, f);
  this.lfo.frequency.setTargetAtTime(q[1] + this.rate * (q[2] - q[1]) || 0.01, t, 0.3);
  this.fade.gain.setTargetAtTime(this.level * (1 - lo / 2), t, 0.3);   // swings between level*(1-lo) and level
  this.depth.gain.setTargetAtTime(this.level * lo / 2, t, 0.3);
};
Voice.prototype.play = function (text) {
  this.cancel();
  if (!AC) return Promise.resolve();
  const tl = timeline(text, this.wpm, this.eff, this.jit), t0 = AC.currentTime + 0.06, g = this.env.gain;
  try { window.__cwPlay = { t: Date.now(), wpm: this.wpm, ms: tl.length ? tl[tl.length - 1][1] * 1000 : 2000 }; } catch (e) {}   /* speed flames (kpc-cw-flames.js) */
  if (this.bug) { // a bug (semi-automatic key): machine dits, hand-made dahs that run long
    const u = 1.2 / this.wpm; let sh = 0;
    tl.marks = tl.marks.map(m => { const len = m[1] - m[0], s0 = m[0] + sh, l2 = len > 2 * u ? len * (1 + this.bug) : len; sh += l2 - len; return [s0, s0 + l2]; }); tl.total += sh;
  }
  g.cancelScheduledValues(t0); g.setValueAtTime(0, t0);
  tl.marks.forEach(m => { g.setTargetAtTime(1, t0 + m[0], RAMP); g.setTargetAtTime(0, t0 + m[1], RAMP); });
  return new Promise(res => { this.done = res; this.timer = setTimeout(() => { this.timer = null; this.done = null; res(); }, (tl.total + 0.12) * 1000); });
};
Voice.prototype.cancel = function () {
  if (this.timer) { clearTimeout(this.timer); this.timer = null; }
  if (AC && this.env) { const t = AC.currentTime; this.env.gain.cancelScheduledValues(t); this.env.gain.setTargetAtTime(0, t, RAMP); }
  if (this.done) { const d = this.done; this.done = null; d(); }
};
Voice.prototype.dispose = function () {
  this.cancel();
  const kill = () => { try { this.osc.stop(); this.lfo && this.lfo.stop(); this.fade.disconnect(); } catch (e) {} };
  setTimeout(kill, 80); VOICES.delete(this);
};
function hushAll() { VOICES.forEach(v => v.dispose()); }

/* ================================================================ Decoder (your sending) */
const dec = {
  unit: 1200 / 18, code: '', text: '', downAt: 0, upAt: 0, timers: [], marks: [], adapt: false,
  reset(unit, adapt) { this.unit = unit; this.adapt = adapt; this.code = ''; this.text = ''; this.clear(); },
  clear() { this.timers.forEach(clearTimeout); this.timers = []; },
  gaps: [],
  down(t) { this.clear(); if (this.upAt && t - this.upAt < 4000) { this.gaps.push(t - this.upAt); if (this.gaps.length > 80) this.gaps.shift(); } this.downAt = t; },
  up(t) {
    const d = t - this.downAt; if (d < 8) return;
    if (!this.adapt) this.unit = 1200 / kw();   // paddles: the keyer's own speed
    const el = d < this.unit * 2 ? '.' : '-';
    if (this.adapt) { // straight key: follow the operator's own speed (5–60 WPM)
      const est = el === '.' ? d : d / 3;
      this.unit = Math.min(240, Math.max(20, this.unit * 0.7 + est * 0.3));
    }
    this.marks.push([el, d]); if (this.marks.length > 60) this.marks.shift();
    this.code += el; this.upAt = t;
    const u = this.unit;
    this.timers.push(setTimeout(() => this.endChar(), u * 2.4));
    this.timers.push(setTimeout(() => { this.text += ' '; ui.live(this.text); }, u * 5.2));
    this.timers.push(setTimeout(() => this.endOver(), Math.max(S.over * 1000, u * 12)));
  },
  endChar() {
    if (!this.code) return;
    const c = DECODE[this.code];
    this.text += c ? c : '*';
    this.code = ''; ui.live(this.text);
    if (MODE === 'games') gameChar(c || '*');
    else if (MODE === 'learn') learnChar(c || '*');
  },
  endOver() {
    this.endChar();
    const t = this.text.trim().replace(/\s+/g, ' ');
    this.text = ''; ui.live('');
    if (t) transmit(t, 'key');
  },
  flush() { this.clear(); this.endOver(); }
};

/* ================================================================ Keys: straight + iambic keyer */
const kw = () => (qrq.on && qrq.kind === 'send') ? qrq.wpm : S.wpm; // keyer speed (the QRQ send ladder sets its own)
const key = { down: false };
function keyDown() { if (key.down) return; key.down = true; sidetone(true); dec.down(performance.now()); ui.lamp(true); }
function keyUp() { if (!key.down) return; key.down = false; sidetone(false); dec.up(performance.now()); ui.lamp(false); }
/* Keyer elements: the tone's start and stop are both set on the sound card's clock, so every dit and dah is exactly
   the right length even when the browser is busy. */
function keyerOn(d, t0) {
  key.down = true;
  if (audio()) { const t = AC.currentTime; myG.gain.cancelScheduledValues(t); myG.gain.setTargetAtTime(1, t, RAMP); myG.gain.setTargetAtTime(0, t + d / 1000, RAMP); }
  dec.down(t0); ui.lamp(true);
}
function keyerOff(t1) { key.down = false; dec.up(t1); ui.lamp(false); }

const ik = { dit: false, dah: false, busy: false, mem: null, last: null, timer: null };
/* Iambic keyer. Mode B remembers the other paddle if you touch it during an element (so a squeeze-and-release
   sends one extra element); mode A only looks at what is held when each element ends. */
function paddle(which, down) { // which: '.' (dit paddle) or '-' (dah paddle)
  if (S.swap) which = which === '.' ? '-' : '.';
  if (which === '.') ik.dit = down; else ik.dah = down;
  if (!down) return;
  if (ik.busy) { if (S.iambic === 'B' && ik.last && which !== ik.last) ik.mem = which; }
  else nextElement();
}
function nextElement() {
  let el = null;
  if (ik.mem) { el = ik.mem; ik.mem = null; }
  else if (ik.dit && ik.dah) el = ik.last === '.' ? '-' : '.';
  else if (ik.dit) el = '.';
  else if (ik.dah) el = '-';
  if (!el) { ik.busy = false; ik.last = null; return; }
  const u = 1200 / kw(), d = el === '.' ? u : 3 * u, t0 = performance.now();
  ik.busy = true; ik.last = el;
  keyerOn(d, t0);
  // timings come from when the element started, not from when the timer happened to fire
  ik.timer = setTimeout(() => { keyerOff(t0 + d); ik.timer = setTimeout(nextElement, Math.max(0, t0 + d + u - performance.now())); }, d);
}
function releaseAll() {
  ik.dit = ik.dah = false; ik.mem = null;
  if (ik.timer) { clearTimeout(ik.timer); ik.timer = null; } ik.busy = false; ik.last = null; keyUp();
}

/* ================================================================ Words, calls and places */
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
const pick = a => a[Math.floor(Math.random() * a.length)];
const chance = p => Math.random() < p;
const AREA = { 1:'CT ME MA NH RI VT', 2:'NJ NY', 3:'DE MD PA', 4:'AL FL GA KY NC SC TN VA', 5:'AR LA MS NM OK TX', 6:'CA',
  7:'AZ ID MT NV OR UT WA WY', 8:'MI OH WV', 9:'IL IN WI', 0:'CO IA KS MN MO NE ND SD' };
const ST_AREA = {}; Object.keys(AREA).forEach(n => AREA[n].split(' ').forEach(s => { ST_AREA[s] = n; }));
const US_ST = Object.keys(ST_AREA).concat(['AK', 'HI']);
const CA_PROV = { ON: 3, QC: 2, BC: 7, AB: 6, MB: 4, SK: 5, NS: 1, NB: 1 };
const STATES = new Set(US_ST.concat(Object.keys(CA_PROV)).concat(['DC', 'PR']));
// hunters near Kentucky show up more often
const ST_WEIGHT = { KY: 6, TN: 4, OH: 4, IN: 4, WV: 2, VA: 3, IL: 3, MO: 2, NC: 3, GA: 2, MI: 2, PA: 2, AL: 2, TX: 2, FL: 2, NY: 2, WI: 1.5, MN: 1, CA: 1.5 };
function randState() {
  const all = US_ST.filter(s => s !== 'AK' && s !== 'HI');
  let tot = 0; const w = all.map(s => { const x = ST_WEIGHT[s] || 0.7; tot += x; return x; });
  let r = Math.random() * tot; for (let i = 0; i < all.length; i++) { r -= w[i]; if (r <= 0) return all[i]; }
  return 'KY';
}
const L = () => String.fromCharCode(65 + rnd(0, 25));
const LX = () => { let c; do { c = L(); } while (c === 'Q' && chance(0.8)); return c; };
function usCall(st) {
  const n = chance(0.88) ? ST_AREA[st] : String(rnd(0, 9));
  const f = rnd(1, 100);
  if (f <= 12) return pick(['K', 'W', 'N']) + n + LX() + LX();                    // 1x2
  if (f <= 42) return pick(['K', 'W', 'N']) + n + LX() + LX() + LX();             // 1x3
  if (f <= 52) return pick(['K', 'W', 'N']) + L() + n + LX() + LX();              // 2x2
  if (f <= 58) return 'A' + 'ABCDEFGHIJKL'[rnd(0, 11)] + n + LX() + LX();          // AA-AL 2x2
  return pick(['K', 'K', 'W', 'N']) + pick('ABCDEFGIJKMNOQ'.split('')) + n + LX() + LX() + LX(); // 2x3
}
function newOp(exclude) {
  let st, call;
  do {
    if (chance(0.05)) { st = pick(Object.keys(CA_PROV)); call = pick(['VE', 'VA']) + CA_PROV[st] + LX() + LX() + (chance(0.5) ? LX() : ''); }
    else { st = randState(); call = usCall(st); }
  } while (exclude && exclude.has(call));
  return { call, st };
}
const NAMES = ['BOB', 'JIM', 'TOM', 'MIKE', 'DAVE', 'JOHN', 'STEVE', 'BILL', 'RON', 'SUE', 'ANN', 'KEN', 'JOE', 'DON', 'GARY', 'LARRY', 'PAT', 'AMY', 'RAY', 'ED'];
function greet() { const h = new Date().getHours(); return h < 12 ? 'GM' : h < 18 ? 'GA' : 'GE'; }
function rst(prog) {
  const r = Math.random();
  if (prog === 'sota') return r < 0.35 ? '5NN' : pick(['579', '559', '569', '549', '539', '449']);
  return r < 0.72 ? '5NN' : pick(['579', '559', '569', '549', '449', '339']);
}
let PLACES = { parks: [['US-1271', 'Taylorsville Lake State Park'], ['US-1257', 'Natural Bridge State Resort Park'], ['US-0724', 'Abraham Lincoln Birthplace NHS']],
  summits: [['W4K/EC-001', 'Black Mountain'], ['W4K/EC-002', 'Little Black Mountain']] };
fetch('kpc-ky-data.json').then(r => r.ok ? r.json() : null).then(d => {
  if (!d) return;
  if (d.parks && d.parks.length) PLACES.parks = d.parks.filter(p => p.c && /^US-\d{4}$/.test(p.c)).map(p => [p.c, p.n]);
  if (d.summits && d.summits.length) PLACES.summits = d.summits.filter(p => p.c).map(p => [p.c, p.n]);
}).catch(() => {});
/* SOTA association prefixes for states near (and a few far from) Kentucky */
const SOTA_ST = { NC: 'W4C/WM', GA: 'W4G/NG', TN: 'W4T/SU', VA: 'W4V/SH', WV: 'W8V/SR', CO: 'W0C/FR', AZ: 'W7A/AE', CA: 'W6/CT' };
function place(prog, st) {
  if (prog === 'sota') {
    if (st === 'KY' || !SOTA_ST[st]) return pick(PLACES.summits);
    return [SOTA_ST[st] + '-' + String(rnd(1, 140)).padStart(3, '0'), ''];
  }
  if (st === 'KY') return pick(PLACES.parks);
  return ['US-' + String(rnd(1, 11000)).padStart(4, '0'), ''];
}

/* ================================================================ Reading what you sent */
const CALLRE = /^(?:[A-Z]{1,2}\d|\d[A-Z]\d?)[A-Z0-9]*[A-Z](?:\/[A-Z0-9]+)?$/;
function norm(s) { return String(s || '').toUpperCase().replace(/<BK>|<BT>|=/g, ' BK ').replace(/<[A-Z]{2}>/g, ' ').replace(/[^A-Z0-9\/?\- ]/g, ' ').replace(/\s+/g, ' ').trim(); }
function toks(s) { const n = norm(s); return n ? n.split(' ') : []; }
function lev(a, b) {
  if (a === b) return 0; const m = a.length, n = b.length; if (!m) return n; if (!n) return m;
  let p = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) { const c = [i]; for (let j = 1; j <= n; j++) c[j] = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); p = c; }
  return p[n];
}
const base = c => String(c).split('/').reduce((x, y) => /\d/.test(y) && y.length >= x.length ? y : x, '');
/* how well does this over match a callsign? 'exact' | 'near' | 'partial' | null */
function callMatch(ts, call) {
  const b = base(call); let best = null;
  for (const t of ts) {
    const q = t.endsWith('?'), w = q ? t.slice(0, -1) : t; if (!w) continue;
    if (!q && (base(w) === b)) return 'exact';
    if (!q && w.length >= 3 && lev(base(w), b) === 1 && CALLRE.test(w)) best = best || 'near';
    if (q && w.length >= 1 && b.indexOf(w) >= 0) best = best || 'partial';
  }
  return best;
}
const isRST = t => /^[1-5][1-9N][1-9N]$/.test(t);
function findRST(ts) { return ts.find(isRST) || null; }
function findState(ts) {
  const i = ts.findIndex(isRST);
  for (let k = Math.max(0, i + 1); k < ts.length; k++) {
    const t = ts[k];
    if (!STATES.has(t)) continue;
    if (t === 'DE' && ts[k + 1] && CALLRE.test(ts[k + 1])) continue;  // "DE W4ABC" is "from", not Delaware
    if (t === 'OR' || t === 'IN' || t === 'ME' || t === 'OK' || t === 'HI') { if (ts[k + 1] === t || ts[k - 1] === t || i >= 0) return t; continue; }
    return t;
  }
  return null;
}
const has = (ts, ...w) => ts.some(t => w.indexOf(t) >= 0);
const asksAgain = ts => has(ts, 'AGN', 'AGN?', '?', 'RPT', 'PSE?', 'AGAIN');
const refRe = /^(US|VE|K|W[0-9A-Z]{0,2})-?\d{3,5}$|^[A-Z0-9]{1,4}\/[A-Z]{2}-\d{3}$/;
const findRef = ts => ts.find(t => refRe.test(t)) || null;

/* ================================================================ UI hooks */
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ui = {
  log(who, text, cls, hidden) {
    const box = $('cwBand'); if (!box) return;
    const row = document.createElement('div'); row.className = 'cw-line ' + (cls || '');
    const show = !hidden || S.show === 'live';
    row.innerHTML = '<span class="who">' + esc(who) + '</span><span class="txt' + (show ? '' : ' hid') + '">' + (show ? esc(text) : '<button type="button" class="reveal">tap to show</button>') + '</span>';
    if (!show) {
      row.dataset.text = text;
      row.querySelector('.reveal').addEventListener('click', () => { row.querySelector('.txt').classList.remove('hid'); row.querySelector('.txt').textContent = text; });
    }
    box.appendChild(row); box.scrollTop = box.scrollHeight;
    while (box.children.length > 160) box.removeChild(box.firstChild);
    return row;
  },
  reveal(row) { if (!row || S.show !== 'after' || !row.dataset.text) return; const t = row.querySelector('.txt'); t.classList.remove('hid'); t.textContent = row.dataset.text; },
  note(text) { const r = ui.log('', text, 'note'); return r; },
  hint(text) { const h = $('cwHint'); if (h) { h.textContent = text || ''; h.hidden = !S.hints || !text; } },
  live(text) { const e = $('cwLive'); if (e) e.textContent = text || ''; },
  lamp(on) { const e = $('cwLamp'); if (e) e.classList.toggle('on', on); document.querySelectorAll('.cw-straight').forEach(b => b.classList.toggle('down', on)); },
  status(text) { const e = $('cwStatus'); if (e) e.textContent = text; },
  stats() { const e = $('cwStats'); if (!e) return; e.innerHTML = statsHtml(); },
  fist() { fistMeter(); }
};

/* ================================================================ Session plumbing */
let GEN = 0, MODE = 'hunt', waiter = null, waitTimer = null, busyThem = 0;
const running = () => MODE !== 'free' && GEN > 0 && session.on;
const session = { on: false, qsos: [], agn: 0, start: 0 };

/* Called when you finish an over (keyed or typed) */
function transmit(text, how) {
  if (MODE === 'qrq') { fistMeter(); qrqSent(text, how); return; }
  if (MODE === 'games' || MODE === 'keyer') { fistMeter(); return; }
  if (MODE === 'learn') { fistMeter(); learnSent(text); return; }
  ui.log('YOU', text, 'you');
  fistMeter();
  if (MODE === 'free' || MODE === 'drill') { ui.hint(''); return; }
  if (!session.on) { ui.hint('Press START to get on the air.'); return; }
  if (waiter) { const w = waiter; waiter = null; clearTimeout(waitTimer); w(text); }
  else if (busyThem) ui.note('They were still sending — wait for their K or BK before you go.');
}
function you(ms) {
  return new Promise(res => {
    waiter = res;
    if (ms) waitTimer = setTimeout(() => { if (waiter === res) { waiter = null; res(null); } }, ms);
  });
}
async function say(v, text, gen) {
  if (gen !== GEN) return;
  busyThem++;
  const row = ui.log(v.call, text, 'them', true);
  try { await v.play(text); } finally { busyThem--; }
  ui.reveal(row);
}
const wait = ms => new Promise(r => setTimeout(r, ms));
function voice(call, opts) {
  const spread = opts && opts.main ? 0 : (chance(0.5) ? -1 : 1) * rnd(60, 320);
  const w = S.match ? S.wpm : Math.max(8, Math.min(35, S.wpm + rnd(-3, opts && opts.main ? 1 : 4)));
  return new Voice({ call, pitch: Math.max(300, Math.min(1100, S.their + spread)), wpm: w, eff: S.match ? S.eff : (S.eff < S.wpm ? Math.max(5, w - (S.wpm - S.eff)) : w),
    jit: opts && opts.main ? 0.04 : Math.random() * 0.12, level: opts && opts.main ? 0.9 : 0.35 + Math.random() * 0.6 });
}
const myCall = () => (S.call || '').toUpperCase().trim() || 'K4TEST';
const progWord = () => S.prog === 'sota' ? 'SOTA' : 'POTA';
const goal = () => S.prog === 'sota' ? 4 : 10;

function stop(silent) {
  GEN++; session.on = false;
  if (waiter) { const w = waiter; waiter = null; clearTimeout(waitTimer); w(null); }
  bandStop(); sprintTimer(false);
  hushAll(); setNoise(false); releaseAll(); dec.clear(); dec.text = ''; dec.code = ''; ui.live('');
  const b = $('cwGo'); if (b) { b.textContent = 'START'; b.classList.remove('stop'); }
  if (!silent) ui.status('Stopped.');
  ui.hint('');
}
function start() {
  if (!audio()) { ui.status('Your browser does not support Web Audio.'); return; }
  if (MODE !== 'free' && MODE !== 'drill' && !CALLRE.test(myCall())) {
    ui.status('Enter your callsign first.'); const c = $('cwCall'); if (c) { c.focus(); c.classList.add('need'); } return;
  }
  stop(true);
  const gen = GEN;
  session.on = true; session.start = Date.now();
  const b = $('cwGo'); if (b) { b.textContent = 'STOP'; b.classList.add('stop'); }
  setNoise(true);
  const go = () => {
    if (gen !== GEN) return;
    if (MODE === 'hunt') hunterLoop(gen).catch(e => console.error(e));
    else if (MODE === 'act') activatorLoop(gen).catch(e => console.error(e));
    else if (MODE === 'chat') chatLoop(gen).catch(e => console.error(e));
    else if (MODE === 'sprint') sprintLoop(gen).catch(e => console.error(e));
    bandStart(gen);
  };
  if (S.welcome && !welcomed) { welcomed = true; welcome(gen).then(go); } else go();
}
/* Zach's welcome, keyed once per visit on the first START (turn it off under the settings) */
const WELCOME = 'HELLO ES WELCOME TO K4ZSR CW ROOM I AM ZACH';
let welcomed = false;
async function welcome(gen) {
  ui.status('Welcome to the K4ZSR CW Room. Zach is on the key… (STOP then START skips it)');
  const v = new Voice({ call: 'K4ZSR', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9 });
  try { await say(v, WELCOME, gen); } finally { v.dispose(); }
  if (gen === GEN) await wait(700);
}

/* ================================================================ You are the HUNTER */
async function hunterLoop(gen) {
  const me = myCall(), P = S.prog, W = progWord();
  let op = newOp(new Set([me]));
  if (P === 'sota') { const st = chance(0.5) ? 'KY' : pick(Object.keys(SOTA_ST)); op = { st, call: usCall(st) }; }
  const pl = place(P, op.st);
  const act = { call: op.call + (P === 'sota' && chance(0.6) ? '/P' : ''), st: op.st, ref: pl[0], name: pl[1] };
  const v = voice(act.call, { main: true });
  ui.status((P === 'sota' ? 'Chasing a SOTA activator' : 'Hunting a POTA activator') + '. Listen for the CQ.');
  ui.note('Tuning in… ' + (P === 'sota' ? 'a summit activator' : 'a park activator') + ' is calling CQ.');
  let first = true, pileOps = [];
  while (gen === GEN) {
    const cq = first ? (chance(0.5) ? `CQ CQ ${W} DE ${act.call} ${act.call} K` : `CQ ${W} CQ ${W} DE ${act.call} ${act.call} K`)
      : (chance(0.6) ? `QRZ ${W} DE ${act.call} K` : `CQ ${W} DE ${act.call} K`);
    first = false;
    await say(v, cq, gen); if (gen !== GEN) return;
    ui.hint(`Send your call once: ${me}` + (S.ref ? `   (at a ${P === 'sota' ? 'summit' : 'park'} too? send ${P === 'sota' ? 'S2S' : 'P2P'} ${me})` : ''));
    // the pileup: other hunters call at the same time
    const n = S.pileN === 0 ? 0 : rnd(Math.max(1, S.pileN - 1), S.pileN + 1);
    pileOps = []; const used = new Set([me, act.call]);
    for (let i = 0; i < n; i++) { const o = newOp(used); used.add(o.call); pileOps.push(Object.assign(o, { v: voice(o.call) })); }
    pileOps.forEach(o => { setTimeout(() => { if (gen === GEN) { busyThem++; o.v.play(o.call + (chance(0.35) ? ' ' + o.call : '')).then(() => busyThem--); } }, rnd(150, 900 + n * 120)); });
    const r = await you(6500 + n * 600);
    if (gen !== GEN) return;
    const ts = toks(r);
    const m = r ? callMatch(ts, me) : null;
    const p2p = has(ts, 'P2P', 'S2S');
    const won = m === 'exact' && (pileOps.length === 0 || chance(p2p ? 0.95 : Math.max(0.3, 0.85 - pileOps.length * 0.06)));
    if (m === 'exact' && !won && pileOps.length) {
      ui.note('The activator picked someone else — stay ready and call again.');
      const o = pick(pileOps); await simQSO(v, act, o, gen); pileOps.forEach(x => x.v.dispose()); continue;
    }
    if (m === 'near') {
      // they half-copied you
      const heard = garble(me);
      pileOps.forEach(x => x.v.dispose());
      await say(v, `${heard}?`, gen); if (gen !== GEN) return;
      ui.hint(`They got part of it. Send your call again, carefully: ${me} ${me}`);
      const r2 = await you(9000); if (gen !== GEN) return;
      if (!r2 || callMatch(toks(r2), me) !== 'exact') { await say(v, 'QRZ?', gen); continue; }
      await exchangeAsHunter(v, act, gen, has(toks(r2), 'P2P', 'S2S') || p2p);
      continue;
    }
    if (!won) {
      if (r && !m) ui.note(`They didn't hear a callsign they could copy. Send just your call: ${me}`);
      if (pileOps.length) { await simQSO(v, act, pick(pileOps), gen); }
      else if (r) { await say(v, chance(0.5) ? 'QRZ?' : 'AGN?', gen); }
      pileOps.forEach(x => x.v.dispose());
      continue;
    }
    pileOps.forEach(x => x.v.dispose());
    await exchangeAsHunter(v, act, gen, p2p);
    if (gen !== GEN) return;
    if (chance(0.25)) { ui.note('The activator is QRT — a new station is calling CQ.'); v.dispose(); return hunterLoop(gen); }
  }
}
function garble(c) {
  const s = c.split(''); const i = rnd(Math.max(1, s.length - 3), s.length - 1);
  const sw = { E: 'I', I: 'S', S: 'H', T: 'M', A: 'W', N: 'D', K: 'R', R: 'K', D: 'B', U: 'V', M: 'O', G: 'Z', P: 'J' };
  s[i] = sw[s[i]] || 'E'; return s.join('');
}
async function exchangeAsHunter(v, act, gen, p2p) {
  const me = myCall(), P = S.prog, theirRst = rst(P), meRef = (S.ref || '').toUpperCase();
  const refPart = (p2p || (P === 'sota' && chance(0.7))) ? ` ${act.ref} ${act.ref}` : '';
  const stPart = P === 'pota' && chance(0.6) ? ` ${act.st} ${act.st}` : '';
  const msg = chance(0.5) ? `${me} ${greet()} UR ${theirRst} ${theirRst}${stPart}${refPart} BK` : `${me} TU UR ${theirRst} ${theirRst}${stPart}${refPart} BK`;
  await say(v, msg, gen); if (gen !== GEN) return;
  const t0 = Date.now();
  ui.hint(`Your turn: BK TU UR 5NN 5NN ${S.st || 'KY'} ${S.st || 'KY'}${p2p && meRef ? ' ' + meRef + ' ' + meRef : ''} BK`);
  let tries = 0, ok = false, gotRst = null, gotSt = null, gotRef = null;
  while (gen === GEN && tries < 4) {
    const r = await you(20000); if (gen !== GEN) return;
    const ts = toks(r);
    if (!r) { await say(v, `${me} ?`, gen); tries++; continue; }
    if (asksAgain(ts) && !findRST(ts)) { session.agn++; await say(v, msg, gen); tries++; continue; }
    if (has(ts, 'PARK?', 'REF?', 'SUMMIT?', 'QTH?', 'PARK', 'REF') && !findRST(ts) && !findRef(ts)) { await say(v, `${act.ref} ${act.ref}${act.name ? '' : ''} BK`, gen); tries++; continue; }
    gotRst = gotRst || findRST(ts); gotSt = gotSt || findState(ts); gotRef = gotRef || findRef(ts);
    if (!gotRst) { await say(v, 'RST?', gen); tries++; ui.hint('They need a signal report — 5NN is fine.'); continue; }
    if (p2p && !gotRef) { await say(v, P === 'sota' ? 'SUMMIT?' : 'PARK?', gen); tries++; ui.hint(`Send your ${P === 'sota' ? 'summit' : 'park'}: ${meRef || (P === 'sota' ? 'W4K/EC-001' : 'US-1271')}`); continue; }
    ok = true; break;
  }
  if (!ok) { await say(v, 'QRZ?', gen); return; }
  const stEcho = gotSt && chance(0.5) ? ` ${gotSt}` : '';
  await say(v, chance(0.5) ? `TU${stEcho} 73 E E` : `R TU${stEcho} 72 E E`, gen);
  logQSO({ call: act.call, sent: gotRst, rcvd: theirRst, st: act.st, ref: act.ref, name: act.name, secs: Math.round((Date.now() - t0) / 1000) });
  ui.hint('Contact logged. Send E E (dit dit) if you like — then listen for the next CQ.');
  const r = await you(2500); if (r === null || gen !== GEN) return;
}
async function simQSO(v, act, o, gen) {
  const a = rst(S.prog), b = rst(S.prog);
  await say(v, `${o.call} ${greet()} UR ${a} ${a} BK`, gen); if (gen !== GEN) return;
  await wait(300);
  busyThem++; const row = ui.log(o.call, `BK TU UR ${b} ${b} ${o.st} ${o.st} BK`, 'them other', true);
  await o.v.play(`BK TU UR ${b} ${b} ${o.st} ${o.st} BK`); busyThem--; ui.reveal(row);
  if (gen !== GEN) return;
  await say(v, `TU 73 E E`, gen);
}

/* ================================================================ You are the ACTIVATOR */
async function activatorLoop(gen) {
  const me = myCall(), P = S.prog, W = progWord();
  const callers = []; const worked = new Set([me]);
  ui.status(`You're ${P === 'sota' ? 'on a summit' : 'in a park'}. Call CQ to start your run — ${goal()} contacts to ${P === 'sota' ? 'qualify the summit' : 'activate the park'}.`);
  ui.hint(`Call CQ: CQ ${W} CQ ${W} DE ${me} ${me} K`);
  let qrs = 0;
  const arrivals = () => {
    const want = Math.max(1, S.pileN); const n = Math.max(0, rnd(Math.max(1, want - 1), want) - callers.length);
    for (let i = 0; i < n; i++) {
      const o = newOp(new Set([...worked, ...callers.map(c => c.call)]));
      o.p2p = chance(0.1); if (o.p2p) { const pl = place(P, o.st); o.ref = pl[0]; }
      o.name = pick(NAMES); o.v = voice(o.call); callers.push(o);
    }
  };
  const callIn = list => {
    list.forEach(o => {
      setTimeout(() => {
        if (gen !== GEN) return;
        busyThem++;
        const txt = (o.p2p ? (P === 'sota' ? 'S2S ' : 'P2P ') : '') + o.call + (chance(0.3) ? ' ' + o.call : '');
        const row = ui.log(o.call, txt, 'them', true);
        o.v.play(txt).then(() => { busyThem--; ui.reveal(row); });
      }, rnd(200, 1300));
    });
  };
  while (gen === GEN) {
    const r = await you(null); if (gen !== GEN) return;
    const ts = toks(r);
    // CQ / QRZ: callers answer
    if (has(ts, 'CQ', 'QRZ', 'QRZ?')) {
      if (has(ts, 'CQ') && !callMatch(ts, me)) { ui.note(`Hunters need your call in the CQ: CQ ${W} DE ${me} K`); continue; }
      arrivals(); callIn(callers);
      ui.hint(`Pick one and send their call with a report: ${callers[0] ? callers[0].call : 'W4ABC'} ${greet()} UR 5NN 5NN ${S.st || 'KY'} BK — or part of a call with ? (like ${callers[0] ? callers[0].call.slice(0, 2) : 'W4'}?)`);
      continue;
    }
    if (!callers.length) { ui.note(`Nobody is calling yet — send CQ ${W} DE ${me} K`); continue; }
    if (asksAgain(ts) && !callers.some(c => callMatch(ts, c.call) === 'exact')) { session.agn++; callIn(callers); continue; }
    if (has(ts, 'QRS')) { qrs += 4; callers.forEach(c => { c.v.wpm = Math.max(6, c.v.wpm - 4); c.v.eff = Math.min(c.v.eff, c.v.wpm); }); }
    // partial call: only matching stations answer
    const QW = ['AGN?', 'QRZ?', 'RST?', 'PSE?', 'QTH?', 'ST?', 'PARK?', 'REF?', 'SUMMIT?', 'NAME?', 'CALL?', 'QRL?'];
    const partial = ts.filter(t => t.endsWith('?') && t.length > 1 && QW.indexOf(t) < 0).map(t => t.slice(0, -1));
    const exact = callers.find(c => callMatch(ts, c.call) === 'exact');
    if (!exact && partial.length) {
      const hit = callers.filter(c => partial.some(p => base(c.call).indexOf(p) >= 0));
      if (hit.length) callIn(hit); else ui.note('No one with that in their call — try QRZ?');
      continue;
    }
    const near = !exact && callers.find(c => callMatch(ts, c.call) === 'near');
    if (near) { await say(near.v, `${near.call} ${near.call}`, gen); ui.hint(`Close! They corrected their call: ${near.call}`); continue; }
    if (!exact) { ui.note('No one recognised their call in that. Send a call you heard, a partial with ?, or QRZ?'); continue; }
    await workHunter(exact, ts, gen);
    if (gen !== GEN) return;
    callers.splice(callers.indexOf(exact), 1); worked.add(exact.call); exact.v.dispose();
    // the callers that are still waiting jump right back in (hunters don't wait for QRZ)
    if (chance(0.5)) arrivals();
    if (callers.length) { await wait(rnd(400, 900)); callIn(callers); }
    ui.hint(callers.length ? `Next! Send a call + report, or QRZ? — ${session.qsos.length}/${goal()} so far.` : `Call CQ again: CQ ${W} DE ${me} K`);
  }
}
async function workHunter(h, ts0, gen) {
  const P = S.prog, me = myCall(), myRef = (S.ref || '').toUpperCase(), t0 = Date.now();
  let ts = ts0, sentRst = findRST(ts);
  let tries = 0;
  while (!sentRst && tries < 3 && gen === GEN) {
    await say(h.v, `${h.call} ${chance(0.5) ? 'UR RST?' : 'RST?'}`, gen); if (gen !== GEN) return;
    ui.hint(`Give them a report: ${h.call} UR 5NN 5NN ${S.st || 'KY'} BK`);
    const r = await you(20000); if (gen !== GEN) return; ts = toks(r); sentRst = findRST(ts); tries++;
  }
  if (!sentRst) return;
  if (h.p2p && !findRef(ts) && myRef) {
    await say(h.v, P === 'sota' ? 'SUMMIT?' : 'PARK?', gen);
    ui.hint(`It's a ${P === 'sota' ? 'summit-to-summit' : 'park-to-park'}. Send your ref: ${myRef} ${myRef} BK`);
    await you(20000); if (gen !== GEN) return;
  }
  const back = rst(P);
  const parts = [chance(0.4) ? 'BK R' : 'BK', chance(0.5) ? `TU ${greet()}` : 'TU', `UR ${back} ${back}`, `${h.st} ${h.st}`];
  if (h.p2p) parts.push(`${h.ref} ${h.ref}`);
  if (chance(0.12)) parts.push(`OP ${h.name}`);
  parts.push('BK');
  const ex = parts.join(' ');
  await say(h.v, ex, gen); if (gen !== GEN) return;
  ui.hint(`Close it out: TU ${h.st} 73 E E   (then QRZ? or call the next one)`);
  let r = null; tries = 0;
  while (gen === GEN && tries < 3) {
    r = await you(20000); if (gen !== GEN) return;
    const t = toks(r);
    if (r && asksAgain(t) && !has(t, 'TU', '73', 'R', 'EE', 'E')) { session.agn++; await say(h.v, ex, gen); tries++; continue; }
    if (r && has(t, 'ST?', 'QTH?')) { await say(h.v, `${h.st} ${h.st}`, gen); tries++; continue; }
    break;
  }
  if (gen !== GEN) return;
  await say(h.v, chance(0.6) ? 'E E' : (chance(0.5) ? '73 E E' : 'TU 73 E E'), gen);
  logQSO({ call: h.call, sent: sentRst, rcvd: back, st: h.st, ref: h.p2p ? h.ref : '', secs: Math.round((Date.now() - t0) / 1000) });
}

/* ================================================================ Log + stats */
function logQSO(q) {
  q.time = new Date(); session.qsos.push(q);
  const tb = $('cwLog'); if (tb) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${session.qsos.length}</td><td>${q.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td><td><b>${esc(q.call)}</b></td><td>${esc(q.sent || '')}</td><td>${esc(q.rcvd || '')}</td><td>${esc(q.st || '')}</td><td>${esc(q.ref || '')}${q.name ? ' <small>' + esc(q.name) + '</small>' : ''}</td><td>${q.secs}s</td>`;
    tb.prepend(tr);
  }
  ui.stats();
  if (MODE === 'act' && session.qsos.length === goal()) ui.note(`🎉 ${goal()} contacts — that's a valid ${S.prog === 'sota' ? 'SOTA activation' : 'POTA activation'}! Keep going for practice.`);
}
function statsHtml() {
  const n = session.qsos.length, secs = session.qsos.reduce((a, q) => a + q.secs, 0);
  const pct = Math.min(100, Math.round(n / goal() * 100));
  return `<div><b>${n}</b><span>contacts</span></div><div><b>${n ? Math.round(secs / n) + 's' : '—'}</b><span>avg per QSO</span></div><div><b>${session.agn}</b><span>repeats asked</span></div>` +
    (MODE === 'act' ? `<div class="bar"><i style="width:${pct}%"></i><span>${Math.min(n, goal())}/${goal()} to ${S.prog === 'sota' ? 'qualify' : 'activate'}</span></div>` : '');
}

/* ================================================================ Fist meter */
function fistMeter() {
  const e = $('cwFist'); if (!e) return;
  const m = dec.marks.slice(-40);
  const dits = m.filter(x => x[0] === '.').map(x => x[1]), dahs = m.filter(x => x[0] === '-').map(x => x[1]);
  if (dits.length < 3 || dahs.length < 2) { e.innerHTML = '<span class="dim">Send a few characters with a key to see your timing.</span>'; return; }
  const av = a => a.reduce((x, y) => x + y, 0) / a.length;
  const sd = a => { const v = av(a); return Math.sqrt(av(a.map(x => (x - v) * (x - v)))) / v; };
  const d = av(dits), h = av(dahs), ratio = h / d, wpm = Math.round(1200 / d);
  try { window.__cwSend = { t: Date.now(), wpm }; } catch (e) {}
  const steady = Math.round(100 - Math.min(60, (sd(dits) + sd(dahs)) * 100));
  const rc = Math.abs(ratio - 3) < 0.45 ? 'good' : Math.abs(ratio - 3) < 0.9 ? 'ok' : 'bad';
  e.innerHTML = `<div><b>${wpm}</b><span>WPM (from your dits)</span></div><div class="${rc}"><b>${ratio.toFixed(1)} : 1</b><span>dah : dit (aim for 3)</span></div><div class="${steady > 80 ? 'good' : steady > 65 ? 'ok' : 'bad'}"><b>${steady}%</b><span>steadiness</span></div>` + fistDoctor(d, h, dits);
}
/* Fist doctor: compare your timing with textbook timing (dit 1, dah 3, gap inside a letter 1, between letters 3, between words 7)
   and say in plain words what to work on. With paddles the keyer times the dits and dahs, so only your spacing counts. */
function fistDoctor(d, h, dits) {
  const pad = S.input === 'iambic', u = pad ? 1200 / kw() : d;
  const g = dec.gaps.slice(-60).map(x => x / u), av = a => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
  const inside = av(g.filter(x => x < 2)), between = av(g.filter(x => x >= 2 && x < 5.5)), words = av(g.filter(x => x >= 5.5 && x < 14));
  const tips = [];
  if (!pad) {
    const ratio = h / d;
    if (ratio < 2.5) tips.push(`Your dahs are short (${ratio.toFixed(1)}× a dit). Hold them a bit longer, about 3 dits.`);
    else if (ratio > 3.6) tips.push(`Your dahs are long (${ratio.toFixed(1)}× a dit). Let go a little sooner.`);
    const sdd = dits.length > 3 ? Math.sqrt(av(dits.map(x => (x - d) * (x - d)))) / d : 0;
    if (sdd > 0.28) tips.push('Your dits are uneven. Try sending a slow, steady string of E\'s and S\'s.');
    if (inside != null && inside > 1.6) tips.push(`The gaps inside your letters are long (${inside.toFixed(1)} dits). Letters may break apart: keep each letter in one smooth motion.`);
  }
  if (between != null && between < 2.4) tips.push(`You run letters together (only ${between.toFixed(1)} dits between letters). Leave a clear pause, about 3 dits.`);
  else if (between != null && between > 4.3) tips.push(`The pauses between your letters are long (${between.toFixed(1)} dits). Close them up to about 3, or they read as word gaps.`);
  if (words != null && words < 6) tips.push(`Your word spaces are short (${words.toFixed(1)} dits). Pause about 7 dits between words.`);
  if (g.length < 6) return '';
  const row = (name, ideal, yours) => yours == null ? '' : `<div class="fd-row"><span>${name}</span><i style="width:${Math.min(100, ideal / 8 * 100)}%"></i><b style="width:${Math.min(100, yours / 8 * 100)}%" class="${Math.abs(yours - ideal) / ideal < 0.2 ? 'good' : Math.abs(yours - ideal) / ideal < 0.4 ? 'ok' : 'bad'}"></b><em>${yours.toFixed(1)}</em></div>`;
  return `<div class="fdoc"><div class="fd-h">FIST DOCTOR <small>gray = textbook, color = you (in dits)</small></div>` +
    (pad ? '' : row('Dah', 3, h / d)) + row('Gap in a letter', 1, inside) + row('Gap between letters', 3, between) + row('Gap between words', 7, words) +
    `<ul>${(tips.length ? tips.slice(0, 3) : ['Nice fist! Your timing is close to textbook.']).map(t => `<li>${esc(t)}</li>`).join('')}</ul></div>`;
}

/* ================================================================ Ragchew: a friendly full QSO
   Name, QTH, rig, antenna and weather, then a proper sign-off. You can send AGN? to hear an over again or QRS to slow them down. */
const TOWNS = { KY: ['BOWLING GREEN', 'LEXINGTON', 'LOUISVILLE', 'PADUCAH', 'PIKEVILLE', 'SOMERSET', 'GLASGOW', 'OWENSBORO', 'MOREHEAD', 'LONDON', 'MURRAY', 'HAZARD', 'ELIZABETHTOWN', 'FRANKFORT', 'CAVE CITY', 'CORBIN'],
  TN: ['NASHVILLE', 'KNOXVILLE', 'CHATTANOOGA', 'MEMPHIS', 'COOKEVILLE', 'JOHNSON CITY'], OH: ['CINCINNATI', 'COLUMBUS', 'DAYTON', 'AKRON', 'ATHENS'],
  IN: ['EVANSVILLE', 'BLOOMINGTON', 'INDIANAPOLIS', 'FORT WAYNE'], WV: ['CHARLESTON', 'HUNTINGTON', 'MORGANTOWN', 'BECKLEY'], VA: ['ROANOKE', 'RICHMOND', 'BRISTOL', 'NORFOLK'],
  IL: ['SPRINGFIELD', 'PEORIA', 'CARBONDALE', 'CHICAGO'], NC: ['ASHEVILLE', 'RALEIGH', 'BOONE', 'CHARLOTTE'], MO: ['ST LOUIS', 'SPRINGFIELD', 'COLUMBIA'], TX: ['AUSTIN', 'DALLAS', 'AMARILLO'],
  GA: ['ATLANTA', 'ATHENS', 'MACON'], MI: ['LANSING', 'GRAND RAPIDS'], PA: ['PITTSBURGH', 'ERIE', 'LANCASTER'], FL: ['TAMPA', 'ORLANDO', 'OCALA'], CA: ['FRESNO', 'SAN DIEGO'] };
const RIGS = ['KX2', 'KX3', 'IC 705', 'FT 891', 'FT 818', 'QMX', 'MTR3B', 'IC 7300', 'K3', 'TS 590', 'FT 991A', 'X6100', 'KH1', 'FT DX10', 'K4'];
const ANTS = ['EFHW', 'DIPOLE', 'VERTICAL', 'G5RV', 'LOOP', 'YAGI', 'OCF DIPOLE', 'HAMSTICK', 'RANDOM WIRE', 'HEXBEAM', 'INV V'];
const WXS = ['SUNNY', 'CLDY', 'RAIN', 'CLEAR', 'WINDY', 'FOGGY', 'PTLY CLDY', 'SNOW'];
const LIKES = ['POTA', 'SOTA', 'CW', 'QRP', 'DX', 'CONTESTS', 'HOMEBREW', 'RAGCHEWING', 'FT8', 'SKCC'];
function wordsAfter(ts, w) { // QTH can be more than one word: take words up to the next break
  const i = ts.indexOf(w); if (i < 0) return '';
  const stop = new Set(['BK', 'KN', 'K', 'ES', 'NAME', 'OP', 'RIG', 'RST', 'UR', 'HW', 'HW?', 'WX', 'ANT', 'PWR', 'DE', 'TNX', 'FER', '73']);
  const out = []; for (let j = i + 1; j < ts.length && out.length < 4; j++) { const t = ts[j]; if (stop.has(t)) break; if ((t === 'IS' || t === 'HR' || t === 'NR') && !out.length) continue; if (/^[A-Z][A-Z]*$/.test(t)) out.push(t); else break; }
  return out.join(' ');
}
function wordAfter(ts, w) { const i = ts.indexOf(w); if (i < 0) return ''; const skip = new Set(['IS', 'HR', 'HERE', 'NR', 'NEAR', 'OP', 'OPR', 'NAME', 'QTH']); for (let j = i + 1; j < Math.min(ts.length, i + 4); j++) { if (!skip.has(ts[j]) && /^[A-Z][A-Z]+$/.test(ts[j])) return ts[j]; } return ''; }
async function chatLoop(gen) {
  const me = myCall(), myName = (S.name || '').toUpperCase().trim() || 'YOURNAME', myQth = (S.qth || '').toUpperCase().trim() || 'YOURTOWN';
  let op; do { op = newOp(new Set([me])); } while (!TOWNS[op.st]); const st = op.st;
  const o = { call: op.call, st, town: pick(TOWNS[st]), name: pick(NAMES), rig: pick(RIGS), pwr: pick([5, 5, 10, 15, 50, 100, 100]), ant: pick(ANTS), wx: '',
    temp: (() => { const m = new Date().getMonth(); return rnd([25, 30, 40, 52, 62, 72, 78, 76, 68, 56, 44, 32][m], [45, 50, 62, 72, 82, 90, 95, 94, 88, 78, 64, 50][m]); })(), yrs: rnd(2, 45), likes: pick(LIKES) };
  o.wx = pick(WXS.filter(w => w !== 'SNOW' || o.temp < 34));
  const v = voice(o.call, { main: true }); let last = '', you2 = { name: '', qth: '' };
  const over = async t => { last = t; await say(v, t, gen); };
  // AGN? repeats the last over; QRS slows them down and repeats; returns the tokens of your real reply (or null)
  const reply = async (hint, ms, quiet) => {
    ui.hint(hint);
    for (let i = 0; i < 6 && gen === GEN; i++) {
      const r = await you(ms || 90000); if (gen !== GEN) return null;
      if (r === null) { if (quiet) return null; await over(`${me} DE ${o.call} ?`); continue; }
      const ts = toks(r);
      if (has(ts, 'QRS')) { v.wpm = Math.max(6, v.wpm - 3); v.eff = Math.min(v.eff, v.wpm); ui.note(`${o.call} slowed down to ${v.wpm} WPM.`); await over('QRS OK ' + last); continue; }
      if (asksAgain(ts) && ts.length <= 4) { session.agn++; await over(last); continue; }
      return ts;
    }
    return null;
  };
  ui.status('Ragchew: a friendly full QSO. Listen for the CQ.');
  // 1) CQ and your answer
  let ts = null;
  for (let n = 0; n < 4 && gen === GEN; n++) {
    await over(`CQ CQ CQ DE ${o.call} ${o.call} K`); if (gen !== GEN) return;
    ts = await reply(`Answer: ${o.call} DE ${me} ${me} K`, 15000, true); if (gen !== GEN) return;
    if (ts && callMatch(ts, me) === 'exact') break;
    if (ts) ui.note(`They didn't copy your call. Send: ${o.call} DE ${me} ${me} K`);
    ts = null;
  }
  if (!ts) { stop(true); ui.note('No contact. Press START to try again.'); return; }
  const t0 = Date.now();
  // 2) their first over: report, QTH, name
  const theirRst = pick(['579', '589', '599', '569', '559']);
  await over(`${me} DE ${o.call} ${greet()} OM ES TNX FER CALL <BT> UR RST ${theirRst} ${theirRst} <BT> QTH ${o.town} ${o.st} ${o.town} ${o.st} <BT> NAME ${o.name} ${o.name} <BT> HW CPY? ${me} DE ${o.call} KN`); if (gen !== GEN) return;
  let gotRst = null;
  for (let tries = 0; tries < 3 && gen === GEN; tries++) {
    ts = await reply(`Your turn: ${o.call} DE ${me} R ${greet()} ${o.name} TNX FER RPT <BT> UR RST 579 579 <BT> QTH ${myQth} <BT> NAME ${myName} <BT> HW? ${o.call} DE ${me} KN`); if (gen !== GEN) return;
    if (!ts) break;
    if (has(ts, '73', 'SK')) break;
    gotRst = gotRst || findRST(ts); you2.name = you2.name || wordAfter(ts, 'NAME') || wordAfter(ts, 'OP'); you2.qth = you2.qth || wordsAfter(ts, 'QTH');
    const need = [!gotRst && 'RST', !you2.name && 'NAME', !you2.qth && 'QTH'].filter(Boolean);
    if (!need.length || tries === 2) break;
    await over(`R R ${need.map(x => x + '?').join(' ')} ${me} DE ${o.call} KN`);
  }
  if (gen !== GEN) return;
  // 3) rig, antenna and weather
  const nm = you2.name || 'OM';
  await over(`R R FB ${nm} ES TNX FER ${gotRst || '5NN'} <BT> ${you2.qth ? 'NICE TO MEET U IN ' + you2.qth + ' <BT> ' : ''}RIG HR IS ${o.rig} ES PWR ${o.pwr}W <BT> ANT IS ${o.ant} <BT> WX HR ${o.wx} ES ${o.temp}F <BT> HW? ${me} DE ${o.call} KN`); if (gen !== GEN) return;
  for (let tries = 0; tries < 2 && gen === GEN; tries++) {
    ts = await reply(`Your turn: R FB ${o.name} <BT> RIG HR IS KX2 ES PWR 5W <BT> ANT IS EFHW <BT> WX ${pick(WXS)} ES 70F <BT> HW? ${o.call} DE ${me} KN`); if (gen !== GEN) return;
    if (!ts || has(ts, '73', 'SK')) break;
    const n = ['RIG', 'ANT', 'WX', 'PWR'].filter(w => ts.includes(w)).length;
    if (n >= 2 || tries === 1) break;
    await over(`R ${n ? '' : 'RIG? '}ANT? WX? ${me} DE ${o.call} KN`);
  }
  if (gen !== GEN) return;
  // 4) a bit of chat, sometimes
  if (ts && !has(ts, '73', 'SK') && chance(0.6)) {
    await over(`FB ${nm} <BT> BEEN A HAM ${o.yrs} YRS ES ENJOY ${o.likes} <BT> HW LONG HAVE U BEEN LICENSED? ${me} DE ${o.call} KN`); if (gen !== GEN) return;
    ts = await reply(`Your turn: R FB <BT> LICENSED 3 YRS ES LUV POTA <BT> ${o.call} DE ${me} KN`); if (gen !== GEN) return;
  }
  // 5) sign-off
  await over(`R TNX FER FB QSO ${nm} <BT> HPE CU AGN <BT> 73 ES GL <SK> ${me} DE ${o.call} TU`); if (gen !== GEN) return;
  ts = await reply(`Sign off: TNX FER QSO ${o.name} 73 <SK> ${o.call} DE ${me} TU`, 30000, true); if (gen !== GEN) return;
  if (ts) await say(v, 'E E', gen);
  const mins = Math.max(1, Math.round((Date.now() - t0) / 60000));
  session.qsos.push({ call: o.call }); ui.stats();
  ui.note(`QSO done (${mins} min). You worked ${o.name}, ${o.call} in ${o.town} ${o.st}: ${o.rig} at ${o.pwr}W, antenna ${o.ant}, WX ${o.wx} ${o.temp}F. Did you copy it all?`);
  v.dispose(); stop(true); ui.status('QSO complete. 73!'); ui.hint('Press START for another ragchew.');
}

/* ================================================================ Real band noise
   'Typical' and 'Rough' add static crashes, a neighbour station a few hundred Hz away and the odd tuner-upper. */
const band = { timers: [], live: [] };
function bandStop() { band.timers.forEach(clearTimeout); band.timers = []; band.live.forEach(n => { try { n.stop(); } catch (e) {} }); band.live = []; }
function crash(rough) {
  if (!AC) return;
  const t = AC.currentTime, len = Math.floor(AC.sampleRate * 0.6), buf = AC.createBuffer(1, len, AC.sampleRate), d = buf.getChannelData(0);
  for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (Math.random() < 0.08 ? 3 : 1);
  const src = AC.createBufferSource(); src.buffer = buf;
  const f = AC.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = S.their; f.Q.value = 0.5;
  const g = AC.createGain(); g.gain.value = 0;
  const pk = (rough ? 0.5 + Math.random() * 0.7 : 0.25 + Math.random() * 0.4), n = rnd(1, rough ? 4 : 2);
  for (let k = 0; k < n; k++) { const s0 = t + k * (0.04 + Math.random() * 0.12); g.gain.setTargetAtTime(pk, s0, 0.002); g.gain.setTargetAtTime(0, s0 + 0.01, 0.03 + Math.random() * 0.08); }
  src.connect(f); f.connect(g); g.connect(master); src.start(t); src.stop(t + 0.6); band.live.push(src);
  src.onended = () => { band.live = band.live.filter(x => x !== src); };
}
function tuneUp(rough) {
  if (!AC) return;
  const t = AC.currentTime, o = AC.createOscillator(), g = AC.createGain(), f0 = rnd(350, 1000), dur = 0.8 + Math.random() * (rough ? 2.5 : 1.5);
  o.frequency.setValueAtTime(f0, t); o.frequency.linearRampToValueAtTime(f0 + rnd(-120, 120), t + dur);
  g.gain.value = 0; g.gain.setTargetAtTime(rough ? 0.3 : 0.18, t, 0.01); g.gain.setTargetAtTime(0, t + dur, 0.01);
  o.connect(g); g.connect(master); o.start(t); o.stop(t + dur + 0.1); band.live.push(o);
  o.onended = () => { band.live = band.live.filter(x => x !== o); };
}
function bandStart(gen) {
  bandStop();
  if (S.bandc === 'clean' || !audio()) return;
  const rough = S.bandc === 'rough', T = (fn, a, b) => band.timers.push(setTimeout(fn, rnd(a, b)));
  const qrn = () => { if (gen !== GEN) return; crash(rough); T(qrn, rough ? 700 : 1800, rough ? 4000 : 8000); };
  const tune = () => { if (gen !== GEN) return; tuneUp(rough); T(tune, rough ? 15000 : 40000, rough ? 40000 : 90000); };
  const qrm = async () => {
    while (gen === GEN) {
      const o = newOp(), v = new Voice({ call: o.call, pitch: Math.max(300, Math.min(1100, S.their + (chance(0.5) ? -1 : 1) * rnd(rough ? 90 : 170, rough ? 260 : 450))), wpm: rnd(16, 32), jit: Math.random() * 0.08, level: rough ? 0.3 + Math.random() * 0.3 : 0.12 + Math.random() * 0.15 });
      await v.play(pick([`CQ CQ DE ${o.call} ${o.call} K`, `${o.call} TU 5NN ${o.st} ${o.st} BK`, `CQ POTA DE ${o.call} K`, `QRZ? DE ${o.call} K`, `R R TNX FER QSO 73 E E`, `UR 579 579 IN ${o.st}`]));
      v.dispose(); if (gen !== GEN) return;
      await wait(rnd(rough ? 400 : 2500, rough ? 3000 : 9000));
    }
  };
  T(qrn, 500, 2500); T(tune, 6000, 20000); band.timers.push(setTimeout(() => { if (gen === GEN) qrm(); }, rnd(1000, 4000)));
}

/* ================================================================ Contest sprint: a timed run (POTA run, CWops CWT, SKCC sprint)
   Score = contacts × different states (the multipliers), like a real contest. */
let SPB = {}; try { SPB = JSON.parse(localStorage.getItem('kpcSprint') || '{}') || {}; } catch (e) { SPB = {}; }
const sp = { end: 0, timer: 0, q: 0, mults: new Set(), busts: 0 };
function spFmt() {
  const me = myCall(), st = S.st || 'KY', nm = (S.name || '').toUpperCase().trim() || 'NAME', nr = (S.nr || '').toUpperCase().trim();
  return {
    pota: { label: 'POTA run', cq: `CQ POTA DE ${me} K`, cqWord: 'POTA', mine: `5NN ${st}`, ex: c => `${c} UR 5NN 5NN ${st} ${st} BK`, ok: ts => !!findRST(ts), ask: 'RST?', their: h => `TU UR ${h.rst} ${h.rst} ${h.st} ${h.st} BK`, rcvd: h => `${h.rst} ${h.st}` },
    cwt: { label: 'CWops CWT', cq: `CQ CWT ${me}`, cqWord: 'CWT', mine: `${nm} ${nr || st}`, ex: c => `${c} ${nm} ${nr || st}`, ok: ts => ts.filter(t => t.length >= 2).length >= 3, ask: 'NR?', their: h => `TU ${h.name} ${h.cwops || h.st}`, rcvd: h => `${h.name} ${h.cwops || h.st}` },
    skcc: { label: 'SKCC sprint', cq: `CQ SKS ${me}`, cqWord: 'SKS', mine: `5NN ${st} ${nm} ${nr || 'NONE'}`, ex: c => `${c} 5NN ${st} ${nm} ${nr || 'NONE'} BK`, ok: ts => !!findRST(ts) && ts.length >= 4, ask: 'AGN?', their: h => `TU 579 ${h.st} ${h.name} ${h.skcc} BK`, rcvd: h => `579 ${h.st} ${h.name} ${h.skcc}` }
  }[S.spFmt] || null;
}
function sprintTimer(on) {
  clearInterval(sp.timer); sp.timer = 0;
  if (!on) return;
  const tick = () => {
    const left = Math.max(0, sp.end - Date.now()), m = Math.floor(left / 60000), s2 = Math.floor(left / 1000) % 60;
    const t = $('spClock'); if (t) t.textContent = `${m}:${String(s2).padStart(2, '0')}`;
    const sc = $('spScore'); if (sc) sc.textContent = `${sp.q} QSOs × ${sp.mults.size} states = ${sp.q * sp.mults.size}`;
    if (!left) sprintDone();
  };
  tick(); sp.timer = setInterval(tick, 250);
}
function spBest() {
  const box = $('spBest'); if (!box) return;
  const k = S.spFmt + S.spMin, b = SPB[k];
  const c = $('spClock'); if (c && !sp.timer) c.textContent = S.spMin + ':00';
  box.textContent = b ? `Your best ${S.spMin}-minute ${(spFmt() || {}).label || ''}: ${b.score} points (${b.q} QSOs, ${b.rate}/hr) on ${b.date}` : 'No sprint score yet for this format and length.';
}
function sprintDone() {
  const q = sp.q, mult = sp.mults.size, score = q * mult, rate = Math.round(q / (S.spMin / 60));
  stop(true);
  const k = S.spFmt + S.spMin, pb = SPB[k], isPB = score > 0 && (!pb || score > pb.score);
  if (isPB) { SPB[k] = { score, q, rate, date: new Date().toISOString().slice(0, 10) }; try { localStorage.setItem('kpcSprint', JSON.stringify(SPB)); } catch (e) {} }
  ui.status('⏱ Time! Sprint over.');
  ui.note(`🏁 ${S.spMin}-minute ${(spFmt() || {}).label}: ${q} QSOs × ${mult} states = ${score} points · rate ${rate} QSOs/hour${sp.busts ? ` · ${sp.busts} call${sp.busts > 1 ? 's' : ''} you had to fix` : ''}${isPB ? ' · 🎉 New personal best!' : ''}`);
  spBest(); const t = $('spClock'); if (t) t.textContent = 'DONE';
}
async function sprintLoop(gen) {
  const F = spFmt(), me = myCall(); if (!F) return;
  const callers = [], worked = new Set([me]);
  Object.assign(sp, { end: Date.now() + S.spMin * 60000, q: 0, mults: new Set(), busts: 0 });
  session.qsos = []; const tb = $('cwLog'); if (tb) tb.innerHTML = ''; ui.stats();
  sprintTimer(true);
  ui.status(`${F.label} sprint: ${S.spMin} minutes. Call CQ and work as many as you can!`);
  ui.hint(`Call CQ: ${F.cq}`);
  const arrivals = () => {
    const want = Math.max(1, S.pileN); const n = Math.max(0, rnd(Math.max(1, want - 1), want) - callers.length);
    for (let i = 0; i < n; i++) {
      const o = newOp(new Set([...worked, ...callers.map(c => c.call)]));
      Object.assign(o, { name: pick(NAMES), rst: rst('pota'), cwops: chance(0.65) ? String(rnd(1, 3700)) : '', skcc: rnd(1, 42000) + pick(['', '', 'C', 'T', 'S']), v: voice(o.call) });
      callers.push(o);
    }
  };
  const callIn = list => list.forEach(o => setTimeout(() => {
    if (gen !== GEN) return; busyThem++;
    const row = ui.log(o.call, o.call, 'them', true);
    o.v.play(o.call).then(() => { busyThem--; ui.reveal(row); });
  }, rnd(150, 900)));
  while (gen === GEN) {
    const r = await you(null); if (gen !== GEN) return;
    const ts = toks(r);
    if (has(ts, 'CQ', 'QRZ', 'QRZ?', 'TEST')) { arrivals(); callIn(callers); ui.hint(`Send a call + your exchange: ${F.ex(callers[0] ? callers[0].call : 'W4ABC')}`); continue; }
    if (!callers.length) { ui.note(`Nobody calling — send ${F.cq}`); continue; }
    if (asksAgain(ts) && !callers.some(c => callMatch(ts, c.call) === 'exact')) { session.agn++; callIn(callers); continue; }
    const partial = ts.filter(t => t.endsWith('?') && t.length > 1 && ['AGN?', 'QRZ?', 'NR?', 'RST?'].indexOf(t) < 0).map(t => t.slice(0, -1));
    const exact = callers.find(c => callMatch(ts, c.call) === 'exact');
    if (!exact && partial.length) { const hit = callers.filter(c => partial.some(p => base(c.call).indexOf(p) >= 0)); if (hit.length) callIn(hit); else ui.note('No one with that in their call. Try QRZ?'); continue; }
    const near = !exact && callers.find(c => callMatch(ts, c.call) === 'near');
    if (near) { sp.busts++; await say(near.v, `${near.call} ${near.call}`, gen); ui.hint(`Fix the call and resend: ${F.ex(near.call)}`); continue; }
    if (!exact) { ui.note('Send a call you heard (or part of one with ?), or QRZ?'); continue; }
    // the exchange
    const h = exact, t0 = Date.now(); let ok = F.ok(ts);
    if (!ok) { await say(h.v, F.ask, gen); if (gen !== GEN) return; ui.hint(`Send your exchange: ${F.mine}`); const r2 = await you(15000); if (gen !== GEN) return; ok = F.ok(toks(r2)) || toks(r2).length >= 2; }
    if (!ok) { ui.note(`${h.call} gave up and moved on.`); callers.splice(callers.indexOf(h), 1); h.v.dispose(); continue; }
    const ex = F.their(h); await say(h.v, ex, gen); if (gen !== GEN) return;
    ui.hint('Send TU (or TU + your call) to log it and bring the next caller');
    let r3 = await you(15000); if (gen !== GEN) return;
    if (r3 && asksAgain(toks(r3)) && !has(toks(r3), 'TU')) { session.agn++; await say(h.v, ex, gen); if (gen !== GEN) return; r3 = await you(15000); if (gen !== GEN) return; }
    logQSO({ call: h.call, sent: F.mine, rcvd: F.rcvd(h), st: h.st, name: '', secs: Math.round((Date.now() - t0) / 1000) });
    sp.q++; sp.mults.add(h.st);
    callers.splice(callers.indexOf(h), 1); worked.add(h.call); h.v.dispose();
    if (r3 && has(toks(r3), 'TU', 'QRZ', 'QRZ?', 'CQ')) { if (chance(0.7)) arrivals(); if (callers.length) callIn(callers); }
    ui.hint(callers.length ? `Next! ${F.ex(callers[0].call)}` : `Call CQ: ${F.cq}`);
  }
}

/* ================================================================ Games
   FALLING LETTERS: with a key or paddles, send each letter before it lands. With the keyboard you hear it and type it.
   BEAT THE CLOCK: send the alphabet, the numbers or your call as fast as you cleanly can. */
let GB = {}; try { GB = JSON.parse(localStorage.getItem('kpcGames') || '{}') || {}; } catch (e) { GB = {}; }
const game = { kind: '', on: false, items: [], raf: 0, last: 0, spawnAt: 0, speed: 0, score: 0, lives: 3, target: '', pos: 0, t0: 0, pen: 0, v: null };
function gSave() { try { localStorage.setItem('kpcGames', JSON.stringify(GB)); } catch (e) {} }
function gameStop(msg) {
  game.on = false; cancelAnimationFrame(game.raf); if (game.v) { game.v.dispose(); game.v = null; }
  const f = $('gmField'); if (f && msg) f.insertAdjacentHTML('beforeend', `<div class="gm-over">${msg}</div>`);
  const b = $('gmGo'); if (b) { b.textContent = '▶ START'; b.classList.remove('stop'); }
  gameShow();
}
function gamePool() {
  const k = ($('gmSet') || {}).value || 'az';
  if (k === 'weak') { const w = weakList(10).map(x => x[0]); if (w.length >= 3) return w; }
  if (k === 'koch') return KOCH.slice(0, Math.max(4, S.kochLevel));
  if (k === 'azn') return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'.split('');
  return 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
}
function gameStart() {
  if (game.on) { gameStop('Stopped.'); return; }
  if (!audio()) return;
  game.kind = (document.querySelector('input[name=gmKind]:checked') || {}).value || 'fall';
  const f = $('gmField'); if (f) f.innerHTML = '';
  dec.text = ''; dec.code = ''; ui.live('');
  if (game.kind === 'clock') {
    if (S.input === 'keyboard') { if (f) f.innerHTML = '<div class="gm-over">Pick Straight key or Paddles under Your Key to play Beat the Clock.</div>'; return; }
    const t = ($('gmClockSet') || {}).value || 'az';
    game.target = t === 'nums' ? '0123456789' : t === 'call' ? (myCall() || 'K4TEST').repeat(3) : t === 'paris' ? 'PARISPARISPARIS' : 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    Object.assign(game, { on: true, pos: 0, t0: 0, pen: 0 });
    clockDraw();
  } else {
    Object.assign(game, { on: true, items: [], score: 0, lives: 3, speed: 28, spawnAt: 0, last: 0 });
    const loop = ts => {
      if (!game.on) return;
      const dt = game.last ? Math.min(0.1, (ts - game.last) / 1000) : 0; game.last = ts;
      const H = (f && f.clientHeight) || 300, W = (f && f.clientWidth) || 300;
      if (ts > game.spawnAt) {
        const pool = gamePool(), c = pick(pool), el = document.createElement('span');
        el.className = 'gm-l' + (S.input === 'keyboard' ? ' hid' : ''); el.textContent = S.input === 'keyboard' ? '?' : c;
        const it = { c, y: -30, x: 10 + Math.random() * Math.max(10, W - 60), el }; el.style.left = it.x + 'px'; f.appendChild(el); game.items.push(it);
        if (S.input === 'keyboard') { if (game.v) game.v.dispose(); game.v = new Voice({ call: 'g', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9, noQsb: true }); game.v.play(c); }
        game.spawnAt = ts + Math.max(900, 3200 - game.score * 60);
      }
      game.speed = 28 + game.score * 1.6;
      for (let i = game.items.length - 1; i >= 0; i--) {
        const it = game.items[i]; it.y += game.speed * dt; it.el.style.transform = `translateY(${it.y}px)`;
        if (it.y > H - 34) { it.el.remove(); game.items.splice(i, 1); game.lives--; f.classList.add('hit'); setTimeout(() => f.classList.remove('hit'), 250); if (game.lives <= 0) { gameFallOver(); return; } }
      }
      gameShow(); game.raf = requestAnimationFrame(loop);
    };
    game.raf = requestAnimationFrame(loop);
  }
  const b = $('gmGo'); if (b) { b.textContent = '■ STOP'; b.classList.add('stop'); }
  gameShow();
  if (S.input === 'keyboard' && game.kind === 'fall') { const i = $('gmType'); if (i) { i.value = ''; i.focus({ preventScroll: true }); } }
}
function gameFallOver() {
  game.items.forEach(it => { it.el.textContent = it.c; it.el.classList.remove('hid'); });
  const k = 'fall-' + (($('gmSet') || {}).value || 'az') + (S.input === 'keyboard' ? '-copy' : '-send'), b = GB[k] || 0, isPB = game.score > b;
  if (isPB) { GB[k] = game.score; gSave(); }
  gameStop(`Game over: <b>${game.score}</b> letters${isPB ? ' · 🎉 New best!' : ` · best ${b}`}`);
}
function gameChar(c) {
  if (!game.on) return;
  if (game.kind === 'clock') {
    const want = game.target[game.pos];
    if (!game.t0) game.t0 = performance.now();
    if (c === want) game.pos++; else game.pen += 2;
    if (game.pos >= game.target.length) {
      const secs = (performance.now() - game.t0) / 1000 + game.pen, k = 'clock-' + (($('gmClockSet') || {}).value || 'az'), b = GB[k], isPB = !b || secs < b;
      if (isPB) { GB[k] = +secs.toFixed(1); gSave(); }
      clockDraw(); gameStop(`Done in <b>${secs.toFixed(1)} s</b>${game.pen ? ` (includes ${game.pen} s for mistakes)` : ''}${isPB ? ' · 🎉 New best!' : ` · best ${b} s`}`);
      return;
    }
    clockDraw(); return;
  }
  const i = game.items.findIndex(it => it.c === c);
  if (i >= 0) { const it = game.items[i]; it.el.classList.add('pop'); setTimeout(() => it.el.remove(), 200); game.items.splice(i, 1); game.score++; }
  gameShow();
}
function clockDraw() {
  const f = $('gmField'); if (!f) return;
  const t = game.target, secs = game.t0 ? ((performance.now() - game.t0) / 1000 + game.pen).toFixed(1) : '0.0';
  f.innerHTML = `<div class="gm-clock"><div class="gm-t">${t.split('').map((c, i) => `<span class="${i < game.pos ? 'ok' : i === game.pos ? 'now' : ''}">${esc(c)}</span>`).join('')}</div><div class="gm-s">${secs} s</div><div class="dim">Send the next letter shown in gold. A wrong letter adds 2 seconds.</div></div>`;
  if (game.on && game.t0) { clearTimeout(game.ct); game.ct = setTimeout(clockDraw, 200); }
}
function gameShow() {
  const set = (id, v) => { const e = $(id); if (e) e.textContent = v; };
  const fall = (document.querySelector('input[name=gmKind]:checked') || {}).value !== 'clock';
  set('gmScore', fall ? String(game.score) : (game.pos + '/' + (game.target.length || 26)));
  set('gmLives', fall ? '❤'.repeat(Math.max(0, game.lives)) + '♡'.repeat(Math.max(0, 3 - game.lives)) : '–');
  document.querySelectorAll('[data-gk]').forEach(e => { e.hidden = e.dataset.gk !== (fall ? 'fall' : 'clock'); });
  const ty = $('gmTypeRow'); if (ty) ty.hidden = !(fall && S.input === 'keyboard');
  const bests = Object.keys(GB).map(k => { const p = k.split('-'); return p[0] === 'clock' ? `Beat the clock (${p[1]}): ${GB[k]} s` : `Falling letters (${p[1]}, ${p[2] === 'copy' ? 'copy' : 'send'}): ${GB[k]}`; });
  const bb = $('gmBest'); if (bb) bb.textContent = bests.length ? 'Your bests: ' + bests.join(' · ') : 'Your bests show here.';
}

/* ================================================================ Activator keyer: big memory buttons for the field
   Plays the message as CW at your speed (sidetone only: it doesn't key a radio). {MY} {THEIR} {REF} {ST} fill in. F1-F8 work too. */
const KDEF = [['CQ', 'CQ POTA CQ POTA DE {MY} {MY} K'], ['MY CALL', '{MY}'], ['REPORT', '{THEIR} TU UR 5NN 5NN {ST} {ST} BK'], ['TU 73', 'TU 73 E E'], ['AGN?', 'AGN?'], ['QRZ?', 'QRZ? DE {MY} K'], ['P2P', 'P2P {REF} {REF}'], ['QRT', 'QRT TNX ALL 73 DE {MY} <SK>']];
let KM = KDEF.map(x => x.slice()); try { const k = JSON.parse(localStorage.getItem('kpcKeyerMem') || 'null'); if (Array.isArray(k) && k.length === 8) KM = k; } catch (e) {}
const keyer = { v: null, i: -1, n: 0 };
function kFill(t) { const th = (($('kyTheir') || {}).value || '').toUpperCase().trim(); return t.replace(/\{MY\}/g, myCall() || 'MYCALL').replace(/\{THEIR\}/g, th || '?').replace(/\{REF\}/g, (S.ref || 'US-0000').toUpperCase()).replace(/\{ST\}/g, S.st || 'KY').replace(/\s+/g, ' ').trim(); }
async function kPlay(i) {
  if (!audio()) return;
  if (keyer.v) { keyer.v.dispose(); keyer.v = null; const was = keyer.i; keyer.i = -1; kDraw(); if (was === i) return; }
  const txt = kFill(KM[i][1]); keyer.i = i; kDraw();
  const out = $('kyOut'); if (out) out.textContent = txt;
  const v = new Voice({ call: 'me', pitch: S.pitch, wpm: S.wpm, eff: S.eff, level: 0.8, noQsb: true }); keyer.v = v;
  await v.play(txt);
  if (keyer.v === v) { v.dispose(); keyer.v = null; keyer.i = -1; kDraw(); }
  if (/\{THEIR\}/.test(KM[i][1]) && /TU/.test(txt)) { keyer.n++; const c = $('kyCount'); if (c) c.textContent = keyer.n; }
}
function kDraw() {
  const g = $('kyGrid'); if (!g) return;
  g.innerHTML = KM.map((m, i) => `<button type="button" class="ky-b${keyer.i === i ? ' on' : ''}" data-i="${i}"><small>F${i + 1}</small>${esc(m[0])}<em>${esc(kFill(m[1]))}</em></button>`).join('');
  g.querySelectorAll('.ky-b').forEach(b => b.addEventListener('click', () => kPlay(+b.dataset.i)));
  const ed = $('kyEdit'); if (ed && !ed.dataset.done) {
    ed.dataset.done = '1';
    ed.innerHTML = KM.map((m, i) => `<div class="ky-e"><b>F${i + 1}</b><input type="text" data-i="${i}" data-f="0" value="${esc(m[0])}" maxlength="10" aria-label="Button ${i + 1} name"><input type="text" data-i="${i}" data-f="1" value="${esc(m[1])}" aria-label="Button ${i + 1} message" autocapitalize="characters" spellcheck="false"></div>`).join('') + '<button type="button" class="cw-small" id="kyReset">RESET TO DEFAULTS</button>';
    ed.querySelectorAll('input').forEach(inp => inp.addEventListener('input', () => { KM[+inp.dataset.i][+inp.dataset.f] = inp.dataset.f === '1' ? inp.value.toUpperCase() : inp.value; try { localStorage.setItem('kpcKeyerMem', JSON.stringify(KM)); } catch (e) {} kDraw(); }));
    $('kyReset').addEventListener('click', () => { KM = KDEF.map(x => x.slice()); try { localStorage.removeItem('kpcKeyerMem'); } catch (e) {} ed.dataset.done = ''; kDraw(); });
  }
}
function kInit() {
  if (!$('kyGrid')) return;
  kDraw();
  const th = $('kyTheir'); if (th) th.addEventListener('input', () => { th.value = th.value.toUpperCase().replace(/\s/g, ''); kDraw(); });
  document.addEventListener('keydown', e => {
    if (MODE !== 'keyer') return;
    const m = /^F([1-8])$/.exec(e.key); if (m) { e.preventDefault(); kPlay(+m[1] - 1); return; }
    if (e.key === 'Escape' && keyer.v) { keyer.v.dispose(); keyer.v = null; keyer.i = -1; kDraw(); }
  });
}

/* ================================================================ Expert Gauntlet: five rounds for seasoned ops
   1 fast copy, 2 cut numbers + tricky calls, 3 pileup from hell, 4 rough band, 5 sloppy fists.
   One AGN per item, no hints, three busts and you're out. Optional weekly version: same rounds for everyone. */
const GR = [null,
  { name: 'Fast copy', how: 'Calls at 35 WPM and up, played once. Type the call.', n: 8 },
  { name: 'Cut numbers & tricky calls', how: 'Type the call and the exchange as numbers: 5NN = 599, T = 0, N = 9, A = 1, E = 5.', n: 6 },
  { name: 'Pileup from hell', how: 'A dozen stations at once, look-alike calls. Type every full call you can pick out (space between them). Two or more right clears it.', n: 4 },
  { name: 'Rough band', how: 'A weak station with deep fading, static and a loud neighbour 100 Hz away. Type the call and exchange.', n: 5 },
  { name: 'Sloppy fists', how: 'A bug with long dahs and a ragged straight key, at speed. Type what they sent.', n: 4 }];
let GPB = {}; try { GPB = JSON.parse(localStorage.getItem('kpcGauntlet') || '{}') || {}; } catch (e) { GPB = {}; }
const gt = { on: false, gen: 0, round: 0, idx: 0, lists: null, busts: 0, pts: 0, agn: 0, v: null, timer: 0, t0: 0, weekly: false, busy: false };
const CUT = { '0': 'T', '9': 'N', '1': 'A', '5': 'E' }, UNCUT = { T: '0', O: '0', N: '9', A: '1', E: '5', U: '2', V: '3', B: '7', D: '8' };
function gtCut(d) { return d.split('').map(c => CUT[c] && chance(0.75) ? CUT[c] : c).join(''); }
function gtNum(tok) { return /^[0-9TONAEUVBD]{3}$/.test(tok) && /[0-9]/.test(tok + '0') ? tok.split('').map(c => UNCUT[c] || c).join('') : tok; }
function gtTricky() {
  const c = newOp().call, k = rnd(1, 7);
  return k === 1 ? pick(['VP2V', 'KP4', 'VE3', 'KH6', 'PJ2', 'ZF2', 'C6A']) + '/' + c : k === 2 ? c + '/P' : k === 3 ? c + '/QRP' : k === 4 ? c + '/M' : k === 5 ? c + '/' + rnd(0, 9) : c;
}
function gtLook(c) { // a look-alike call: one letter or digit changed
  const i = rnd(1, c.length - 1), ch = c[i], al = /\d/.test(ch) ? '0123456789' : 'ABDEHIKNRSTUVW';
  let n; do { n = pick(al.split('')); } while (n === ch); return c.slice(0, i) + n + c.slice(i + 1);
}
function gtBuild() {
  const L = [null, [], [], [], [], []];
  for (let i = 0; i < GR[1].n; i++) L[1].push({ text: newOp().call, wpm: 35 + i });
  for (let i = 0; i < GR[2].n; i++) { const c = gtTricky(), ser = String(rnd(1, 999)).padStart(3, '0'); L[2].push({ text: `${c} 5NN ${gtCut(ser)}`, ans: `${c} 599 ${ser}`, wpm: 30 + i }); }
  for (let i = 0; i < GR[3].n; i++) {
    const base = newOp().call, set = new Set([base]); const looks = rnd(2, 3);
    for (let k = 0; k < looks; k++) set.add(gtLook(base));
    while (set.size < rnd(9, 12)) set.add(newOp().call);
    L[3].push({ calls: [...set].map(c => ({ c, wpm: rnd(26, 36), d: rnd(0, 700), p: rnd(-35, 35), twice: chance(0.4) })) });
  }
  for (let i = 0; i < GR[4].n; i++) { const o = newOp(); L[4].push({ text: `${o.call} 5NN ${o.st}`, wpm: 26 + i }); }
  const msgs = () => { const nm = pick(NAMES), st = pick(['TX', 'OH', 'KY', 'TN', 'MI', 'NC']); return pick([`R R TNX FER CALL UR 579 579 IN ${st}`, `NAME HR IS ${nm} ${nm} QTH NR ${pick(TOWNS.KY)}`, `RIG IS ${pick(RIGS)} ES ANT IS ${pick(ANTS)}`, `WX HR ${pick(WXS)} ES ${rnd(30, 90)}F HW CPY`, `TU ${nm} 73 ES GL CU AGN`]); };
  for (let i = 0; i < GR[5].n; i++) L[5].push({ text: msgs(), wpm: 24 + i * 2, bug: i % 2 === 0 ? 0.45 : 0, jit: i % 2 === 0 ? 0.06 : 0.3 });
  return L;
}
function gtShow(msg) {
  const set = (id, v) => { const e = $(id); if (e) e.textContent = v; };
  set('gtRound', gt.round ? gt.round + ' / 5' : '–'); set('gtBusts', '✖'.repeat(gt.busts) + '○'.repeat(Math.max(0, 3 - gt.busts))); set('gtPts', String(gt.pts));
  const it = gt.on && gt.lists && gt.round ? `${Math.min(gt.idx + 1, GR[gt.round].n)} of ${GR[gt.round].n}` : '–'; set('gtItem', it);
  const go = $('gtGo'); if (go) { go.textContent = gt.on ? '■ STOP' : '⚔️ START THE GAUNTLET'; go.classList.toggle('stop', gt.on); }
  const ag = $('gtAgn'); if (ag) ag.disabled = !gt.on || gt.agn >= 1 || gt.busy;
  if (msg != null) { const f = $('gtFb'); if (f) f.innerHTML = msg; }
  const b = $('gtBest'); if (b) {
    const wk = GPB.weeks && GPB.weeks[weekId()], best = GPB.best;
    b.innerHTML = (best ? `Your best: <b>${best.pts} points</b>, reached round ${best.round}${best.cleared ? ' · ⚔️ GAUNTLET CLEARED' : ''}` : 'No gauntlet run yet.') + (wk ? ` · This week: <b>${wk.pts}</b>` : '') + (best ? ' <button type="button" class="cw-small" id="gtShare">📣 SHARE</button><span class="dim" id="gtShared"></span>' : '') + (wk ? ' <a class="cw-small" id="gtSubmit" hidden target="_blank" rel="noopener">🏆 SUBMIT THIS WEEK\'S SCORE</a>' : '');
    if (wk && window.KPCCWBoard) KPCCWBoard.ready.then(() => { const a = $('gtSubmit'), u = KPCCWBoard.link('gauntlet', weekId(), wk.pts, wk.round, S.call); if (a && u) { a.href = u; a.hidden = false; } });
    const sh = $('gtShare'); if (sh) sh.onclick = async () => { const txt = `${myCall() || 'I'} scored ${best.pts} on the KPC Expert CW Gauntlet (round ${best.round} of 5${best.cleared ? ', cleared it!' : ''}) ⚔️ https://kentuckyportableclub.github.io/KPC-Links/kpc-cw.html#gaunt`; const o = $('gtShared'); try { if (navigator.share) { await navigator.share({ text: txt }); return; } await navigator.clipboard.writeText(txt); if (o) o.textContent = ' Copied.'; } catch (e) { if (o) o.textContent = ' ' + txt; } };
  }
}
function gtEnv(on) { // round 4: loud hiss, static crashes and a loud neighbour
  bandStop(); if (gt.qrm) { gt.qrm.dispose(); gt.qrm = null; }
  if (!AC) return;
  noiseG.gain.setTargetAtTime(on ? 0.22 : (gt.on ? 0.03 : 0), AC.currentTime, 0.1);
  if (!on) return;
  const g = gt.gen;
  const qrn = () => { if (g !== gt.gen) return; crash(true); band.timers.push(setTimeout(qrn, rnd(600, 2500))); }; qrn();
  const qrm = async () => { while (g === gt.gen) { const o = newOp(); gt.qrm = new Voice({ call: o.call, pitch: S.their + 100, wpm: rnd(22, 30), level: 0.85, noQsb: true }); await gt.qrm.play(`CQ TEST ${o.call} ${o.call} TEST`); if (gt.qrm) gt.qrm.dispose(); gt.qrm = null; await wait(rnd(100, 600)); } }; qrm();
}
function gtStop(msg) {
  gt.on = false; gt.gen++; clearTimeout(gt.timer); if (gt.v) { gt.v.forEach ? gt.v.forEach(v => v.dispose()) : gt.v.dispose(); gt.v = null; }
  gtEnv(false); if (AC) noiseG.gain.setTargetAtTime(0, AC.currentTime, 0.1);
  gtShow(msg);
}
function gtStart() {
  if (gt.on) { gtStop('Stopped.'); return; }
  if (!audio()) return;
  gt.weekly = !!($('gtWeekly') || {}).checked;
  const id = weekId();
  gt.lists = gt.weekly ? seeded(id.split('').reduce((h, c) => (h * 33 + c.charCodeAt(0)) >>> 0, 11) + 99, gtBuild) : gtBuild();
  Object.assign(gt, { on: true, gen: gt.gen + 1, round: 0, idx: 0, busts: 0, pts: 0 });
  gtRound(1);
}
async function gtRound(n) {
  const g = gt.gen; gt.round = n; gt.idx = 0;
  gtEnv(n === 4);
  gtShow(`<div class="gt-intro"><b>ROUND ${n}: ${GR[n].name.toUpperCase()}</b><br>${GR[n].how}</div>`);
  await wait(2600); if (g !== gt.gen) return;
  gtItem();
}
async function gtItem() {
  const g = gt.gen; gt.agn = 0;
  const a = $('gtIn'); if (a) { a.value = ''; a.focus({ preventScroll: true }); }
  gtShow(); await gtPlay(); if (g !== gt.gen) return;
  clearTimeout(gt.timer); gt.t0 = Date.now();
  gt.timer = setTimeout(() => { if (g === gt.gen) gtJudge(true); }, gt.round === 3 ? 45000 : 30000);
}
async function gtPlay() {
  const it = gt.lists[gt.round][gt.idx]; if (!it) return;
  if (gt.v) { gt.v.forEach ? gt.v.forEach(v => v.dispose()) : gt.v.dispose(); gt.v = null; }
  gt.busy = true; gtShow();
  try {
    if (gt.round === 3) {
      const vs = it.calls.map(c => new Voice({ call: c.c, pitch: S.their + c.p, wpm: c.wpm, jit: 0.05, level: 0.35 + Math.random() * 0.5, noQsb: true })); gt.v = vs;
      await Promise.all(vs.map((v, i) => wait(it.calls[i].d).then(() => v.play(it.calls[i].twice ? it.calls[i].c + ' ' + it.calls[i].c : it.calls[i].c))));
    } else {
      const v = new Voice({ call: 'gt', pitch: S.their, wpm: it.wpm, eff: it.wpm, jit: it.jit || 0.02, bug: it.bug || 0, level: gt.round === 4 ? 0.3 : 0.9, noQsb: gt.round !== 4, fade: gt.round === 4 ? 4 : undefined });
      gt.v = v; await v.play(it.text);
    }
  } finally { gt.busy = false; gtShow(); }
}
function gtAgn() { if (!gt.on || gt.agn >= 1 || gt.busy) return; gt.agn++; clearTimeout(gt.timer); const g = gt.gen; gtPlay().then(() => { if (g !== gt.gen) return; gt.timer = setTimeout(() => { if (g === gt.gen) gtJudge(true); }, 30000); }); }
function gtJudge(timeout) {
  if (!gt.on) return;
  clearTimeout(gt.timer);
  const it = gt.lists[gt.round][gt.idx], a = $('gtIn'), got = norm(a ? a.value : '');
  if (!timeout && !got) return;
  let ok = false, msg = '';
  if (gt.round === 3) {
    const calls = new Set(it.calls.map(c => c.c)), typed = [...new Set(got.split(' ').filter(Boolean))];
    const right = typed.filter(t => calls.has(t)), wrong = typed.filter(t => !calls.has(t));
    ok = right.length >= 2; gt.pts += right.length * 15 - wrong.length * 5;
    msg = `${ok ? '<div class="good">✓' : '<div class="bad">✗'} ${right.length} right${wrong.length ? `, ${wrong.length} busted (${esc(wrong.join(' '))})` : ''}</div><div class="dim">In the pile: ${esc([...calls].join(' '))}</div>`;
  } else if (gt.round === 5) {
    const want = norm(it.text), d = lev(want.replace(/ /g, ''), got.replace(/ /g, '')), acc = Math.max(0, 1 - d / want.replace(/ /g, '').length);
    ok = acc >= 0.8; if (ok) gt.pts += Math.round(acc * it.wpm * 3);
    msg = `${ok ? '<div class="good">✓' : '<div class="bad">✗'} ${Math.round(acc * 100)}% copied</div><div class="dim">They sent: ${esc(want)}</div>`;
  } else {
    const want = norm(it.ans || it.text);
    const fix = s => s.split(' ').map((t, i) => i === 0 ? t : gtNum(t)).join(' ');
    ok = fix(got) === fix(want); if (ok) gt.pts += Math.round(it.wpm * want.replace(/ /g, '').length / 5 * gt.round);
    msg = `${ok ? '<div class="good">✓ ' + esc(want) : '<div class="bad">✗ It was ' + esc(want)}</div>${!ok && got ? `<div class="dim">You typed: ${esc(got)}</div>` : ''}`;
  }
  if (timeout && !ok) msg = '<div class="bad">⏱ Out of time.</div>' + msg;
  if (!ok) gt.busts++;
  gtShow(msg);
  const g = gt.gen;
  if (gt.busts >= 3) { setTimeout(() => { if (g === gt.gen) gtFinish(false); }, 1800); return; }
  gt.idx++;
  setTimeout(() => {
    if (g !== gt.gen) return;
    if (gt.idx >= GR[gt.round].n) { gt.pts += 100 * gt.round; if (gt.round >= 5) { gtFinish(true); return; } gtRound(gt.round + 1); }
    else gtItem();
  }, ok ? 1100 : 2400);
}
function gtFinish(cleared) {
  const pts = gt.pts, round = gt.round, best = GPB.best, isPB = !best || pts > best.pts;
  if (isPB) GPB.best = { pts, round, cleared, date: new Date().toISOString().slice(0, 10) };
  if (gt.weekly) { GPB.weeks = GPB.weeks || {}; const w = GPB.weeks[weekId()]; if (!w || pts > w.pts) GPB.weeks[weekId()] = { pts, round, cleared }; }
  try { localStorage.setItem('kpcGauntlet', JSON.stringify(GPB)); } catch (e) {}
  gtStop(`<div class="qrq-end">${cleared ? '⚔️ <b>GAUNTLET CLEARED!</b> All five rounds.' : `Three busts. Out in round ${round}: <b>${GR[round].name}</b>.`}<br><b>${pts} points</b>${isPB ? ' · 🎉 New personal best!' : ''}</div>`);
}

/* ================================================================ Learn CW: from scratch to 30 WPM, copy AND send
   Koch order, two new characters in lesson 1 then one per lesson. Each lesson: MEET it, COPY (hear it, tap/type it:
   90% of 20) and SEND (key it: 90% of 10). Characters always at 20 WPM; Farnsworth spacing starts wide and closes.
   Then words and calls, then speed steps up to 30 WPM. Progress on this device only (localStorage kpcLearn). */
let _LS = null; const LSF = () => _LS || (_LS = (() => {
  const out = [];
  for (let i = 1; i < KOCH.length; i++) out.push({ id: 'c' + i, kind: 'char', n: i + 1, newc: i === 1 ? [KOCH[0], KOCH[1]] : [KOCH[i]], cw: 20, ew: 8 + Math.floor(i / 8) });
  out.push({ id: 'w1', kind: 'words', title: 'Common CW words', cw: 20, ew: 10, src: 'words' });
  out.push({ id: 'w2', kind: 'words', title: 'Call signs', cw: 20, ew: 12, src: 'calls' });
  out.push({ id: 'w3', kind: 'words', title: 'POTA exchanges', cw: 20, ew: 13, src: 'exch' });
  [15, 18, 20].forEach(e => out.push({ id: 'f' + e, kind: 'words', title: `Speed: ${e} WPM`, cw: 20, ew: e, src: 'mix' }));
  [22, 24, 26, 28, 30].forEach(w => out.push({ id: 's' + w, kind: 'words', title: `Speed: ${w} WPM`, cw: w, ew: w, src: 'mix' }));
  return out;
})());
let LC = { at: 0, done: {} }; try { Object.assign(LC, JSON.parse(localStorage.getItem('kpcLearn') || '{}')); } catch (e) {}
const lsave = () => { try { localStorage.setItem('kpcLearn', JSON.stringify(LC)); } catch (e) {} };
const ln = { part: 'meet', item: '', hist: [], v: null, busy: false };
const lsetChars = st => KOCH.slice(0, st.kind === 'char' ? st.n : KOCH.length);
const pat = c => (PROSIGN[c] || MORSE[c] || '').replace(/\./g, '·').replace(/-/g, '−');
const LWORDS = ['CQ', 'DE', 'TU', '73', '5NN', 'RST', 'UR', 'ES', 'FB', 'OM', 'GM', 'GA', 'GE', 'NAME', 'QTH', 'WX', 'RIG', 'ANT', 'PWR', 'AGN', 'QRZ', 'BK', 'TNX', 'HR', 'POTA', 'SOTA', 'PARK', 'KY', 'TEST', 'THE', 'AND', 'YOU', 'ARE', 'GOOD', 'SUN', 'RAIN', 'COLD', 'HOT', 'KEY', 'HAM', 'CLUB', 'LAKE', 'HILL', 'TREE', 'DOG', 'CAT', 'FUN', 'WIRE'];
function lItem(st) {
  if (st.kind === 'char') { const set = lsetChars(st); return chance(0.4) ? pick(st.newc) : pick(set); }
  const k = st.src === 'mix' ? pick(['words', 'calls', 'exch', 'calls']) : st.src;
  if (k === 'calls') return newOp().call;
  if (k === 'exch') { const o = newOp(); return pick([`${o.call} 5NN ${o.st}`, `TU 5NN ${o.st} ${o.st}`, `UR 5NN ${o.st} BK`, `CQ POTA DE ${o.call} K`]); }
  return pick(LWORDS) + (chance(0.4) ? ' ' + pick(LWORDS) : '');
}
const lneed = () => ln.part === 'send' ? 10 : 20;
function lScore() { const h = ln.hist.slice(-lneed()); return { n: h.length, ok: h.filter(Boolean).length }; }
function learnDraw() {
  const box = $('lnBody'); if (!box) return;
  const st = LSF()[LC.at] || LSF()[0], i = LC.at;
  const total = LSF().length, doneN = Object.keys(LC.done).length;
  $('lnMap').innerHTML = LSF().map((x, k) => `<button type="button" class="ln-dot${k === i ? ' on' : ''}${LC.done[x.id] ? ' done' : ''}" data-k="${k}" title="${x.kind === 'char' ? 'Lesson ' + (k + 1) + ': ' + x.newc.join(' ') : x.title}">${x.kind === 'char' ? esc(x.newc[x.newc.length - 1]) : x.id[0] === 'w' ? '✎' : '⚡'}</button>`).join('');
  $('lnMap').querySelectorAll('.ln-dot').forEach(b => b.addEventListener('click', () => { LC.at = +b.dataset.k; lsave(); learnGo('meet'); }));
  $('lnProg').textContent = `${doneN} of ${total} steps done · ${st.kind === 'char' ? `Lesson ${i + 1}: you know ${st.n} characters` : st.title} · characters at ${st.cw} WPM, spacing ${st.ew} WPM`;
  const tabs = ['meet', 'copy', 'send'].map(p => `<button type="button" class="ln-part${ln.part === p ? ' on' : ''}" data-p="${p}">${p === 'meet' ? '1 · MEET' : p === 'copy' ? '2 · COPY' : '3 · SEND'}</button>`).join('');
  let body = '';
  if (ln.part === 'meet') {
    if (st.kind === 'char') body = `<div class="ln-meet">${st.newc.map(c => `<div class="ln-card"><b>${esc(c)}</b><span>${pat(c)}</span><button type="button" class="cw-small" data-hear="${esc(c)}">▶ HEAR IT</button></div>`).join('')}</div>
      <p class="dim">Learn the <b>sound</b>, not the dots and dashes: listen a few times and say it in your head ("di-dah" for A). Then practice copying and sending. You already know: <b>${esc(lsetChars(st).join(' '))}</b></p>`;
    else body = `<p>${esc(st.title)}: real words and calls at <b>${st.cw} WPM</b> characters${st.ew < st.cw ? ` with extra space between them (${st.ew} WPM overall)` : ''}. Copy 90% of 20, then send 90% of 10.</p><p><button type="button" class="cw-small" id="lnSample">▶ HEAR A SAMPLE</button></p>`;
    body += `<button type="button" class="cw-btn" id="lnNext">NEXT: COPY PRACTICE →</button>`;
  } else {
    const sc = lScore(), pct = sc.n ? Math.round(sc.ok / sc.n * 100) : 0;
    const bar = `<div class="ln-bar"><i style="width:${Math.min(100, sc.n / lneed() * 100)}%"></i></div><div class="dim">${sc.ok}/${sc.n} right (${pct}%) · need 90% of ${lneed()} to pass</div>`;
    if (ln.part === 'copy') {
      const grid = st.kind === 'char' ? `<div class="ln-grid">${lsetChars(st).map(c => `<button type="button" class="ln-k" data-c="${esc(c)}">${esc(c)}</button>`).join('')}</div>` : `<div class="cw-typerow"><input type="text" id="lnIn" autocomplete="off" autocapitalize="characters" spellcheck="false" placeholder="Type what you heard, Enter" aria-label="Type what you heard"><button type="button" class="cw-btn" id="lnOk">CHECK</button></div>`;
      body = `<div class="row"><button type="button" class="cw-btn" id="lnPlay">▶ PLAY</button><button type="button" class="cw-small" id="lnRep">↻ AGAIN</button></div>${grid}<div id="lnFb"></div>${bar}`;
    } else {
      body = (S.input === 'keyboard' ? '<p class="bad">Pick <b>Straight key</b> or <b>Paddles</b> under Your Key (on a phone, use the big DIT/DAH pads; on a computer the mouse paddle works too).</p>' : '') +
        `<div class="ln-target"><small>SEND THIS</small><b id="lnT">${esc(ln.item)}</b>${ln.item.length === 1 ? `<span>${pat(ln.item)}</span>` : ''}</div><div class="row"><button type="button" class="cw-small" id="lnHearT">▶ HEAR IT FIRST</button><button type="button" class="cw-small" id="lnSkip">NEW ONE</button></div><div id="lnFb"></div>${bar}`;
    }
  }
  box.innerHTML = `<div class="ln-parts">${tabs}</div>${body}`;
  box.querySelectorAll('.ln-part').forEach(b => b.addEventListener('click', () => learnGo(b.dataset.p)));
  box.querySelectorAll('[data-hear]').forEach(b => b.addEventListener('click', () => lPlay(b.dataset.hear, st)));
  const on = (id, f) => { const e = $(id); if (e) e.addEventListener('click', f); };
  on('lnNext', () => learnGo('copy')); on('lnSample', () => lPlay(lItem(st), st));
  on('lnPlay', () => { ln.item = lItem(st); lPlay(ln.item, st); }); on('lnRep', () => ln.item && lPlay(ln.item, st));
  on('lnOk', () => lCheck(($('lnIn') || {}).value || '')); const li = $('lnIn'); if (li) { li.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); lCheck(li.value); } }); }
  box.querySelectorAll('.ln-k').forEach(b => b.addEventListener('click', () => lCheck(b.dataset.c)));
  on('lnHearT', () => lPlay(ln.item, st)); on('lnSkip', () => { ln.item = lItem(st); learnDraw(); });
}
async function lPlay(t, st) {
  if (!audio() || !t) return;
  if (ln.v) ln.v.dispose();
  ln.v = new Voice({ call: 'ln', pitch: S.their, wpm: st.cw, eff: st.ew, jit: 0, level: 0.9, noQsb: true });
  ln.busy = true; try { await ln.v.play(t); } finally { ln.busy = false; }
}
function learnGo(part) {
  ln.part = part; ln.hist = []; ln.item = '';
  const st = LSF()[LC.at];
  if (part === 'send') { ln.item = lItem(st); dec.text = ''; dec.code = ''; dec.reset(S.input === 'iambic' ? 1200 / S.wpm : 1200 / 15, S.input === 'straight'); }
  learnDraw();
  if (part === 'copy') setTimeout(() => { ln.item = lItem(st); lPlay(ln.item, st); }, 300);
}
function lResult(ok, msg) {
  const st = LSF()[LC.at]; ln.hist.push(ok);
  const sc = lScore();
  const fb = () => { const f = $('lnFb'); if (f) f.innerHTML = msg; };
  if (sc.n >= lneed() && sc.ok / sc.n >= 0.9) {
    if (ln.part === 'copy') { learnGo('send'); const f = $('lnFb'); if (f) f.innerHTML = '<div class="good">✓ Copy passed! Now send it.</div>'; return; }
    LC.done[st.id] = new Date().toISOString().slice(0, 10); if (LC.at < LSF().length - 1) LC.at++; lsave();
    learnGo('meet'); const f = $('lnFb') || $('lnBody'); if (f) f.insertAdjacentHTML('afterbegin', `<div class="ln-pass">⭐ Step passed! ${LC.at >= LSF().length - 1 && LC.done[LSF()[LSF().length - 1].id] ? 'You made it to 30 WPM! 🎉' : 'On to the next one.'}</div>`);
    return;
  }
  learnDraw(); fb();
}
function lCheck(got) {
  if (ln.part !== 'copy' || !ln.item || ln.busy) return;
  const st = LSF()[LC.at], ch = st.kind === 'char', want = ch ? ln.item : norm(ln.item), g = ch ? String(got).toUpperCase().trim() : norm(got), ok = want === g;
  if (!ch) trackCopy(want, g); else if (/^[A-Z0-9]$/.test(want)) trackCopy(want, g);
  lResult(ok, ok ? `<div class="good">✓ ${esc(want)}</div>` : `<div class="bad">✗ It was ${esc(want)}${want.length === 1 ? ' ' + pat(want) : ''}</div>`);
  setTimeout(() => { if (ln.part === 'copy' && MODE === 'learn') { ln.item = lItem(st); lPlay(ln.item, st); } }, ok ? 700 : 1600);
}
function learnChar(c) { if (ln.part !== 'send' || ln.item.length !== 1) return; lSendResult(c === ln.item, c); }
function learnSent(text) { if (ln.part !== 'send' || ln.item.length === 1) return; lSendResult(norm(text) === norm(ln.item), norm(text)); }
function lSendResult(ok, got) {
  const st = LSF()[LC.at], want = ln.item;
  ln.item = lItem(st); dec.text = ''; ui.live('');
  lResult(ok, ok ? `<div class="good">✓ Clean ${esc(want)}</div>` : `<div class="bad">✗ That came out as "${esc(got)}". ${want.length === 1 ? esc(want) + ' is ' + pat(want) : ''}</div>`);
}

/* ================================================================ Problem letters
   Every copy check (drills and the QRQ copy ladder) counts which characters you missed. */
let MISS = {}; try { MISS = JSON.parse(localStorage.getItem('kpcCWmiss') || '{}') || {}; } catch (e) { MISS = {}; }
function trackCopy(want, got) {
  want = norm(want).replace(/ /g, ''); got = norm(got).replace(/ /g, '');
  if (!want) return;
  // line up what you typed with what was sent (longest common subsequence), so one extra letter doesn't spoil the rest
  const m = want.length, n = got.length, d = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = m - 1; i >= 0; i--) for (let j = n - 1; j >= 0; j--) d[i][j] = want[i] === got[j] ? d[i + 1][j + 1] + 1 : Math.max(d[i + 1][j], d[i][j + 1]);
  const hit = new Array(m).fill(false); let i = 0, j = 0;
  while (i < m && j < n) { if (want[i] === got[j]) { hit[i] = true; i++; j++; } else if (d[i + 1][j] >= d[i][j + 1]) i++; else j++; }
  for (let k = 0; k < m; k++) { const c = want[k]; const e = MISS[c] || (MISS[c] = { n: 0, m: 0 }); e.n++; if (!hit[k]) e.m++; }
  try { localStorage.setItem('kpcCWmiss', JSON.stringify(MISS)); } catch (e) {}
  weakShow();
}
function weakList(k) { return Object.keys(MISS).filter(c => MISS[c].n >= 3 && MISS[c].m > 0).map(c => [c, MISS[c].m / MISS[c].n, MISS[c].n]).sort((a, b) => b[1] - a[1]).slice(0, k || 8); }
function weakShow() {
  const box = $('cwWeak'); if (!box) return;
  const w = weakList(8), seen = Object.keys(MISS).reduce((t, c) => t + MISS[c].n, 0);
  if (!w.length) { box.innerHTML = `<b>YOUR PROBLEM LETTERS</b> <span class="dim">${seen ? 'None yet. Nice copying!' : 'Copy a few drills and the letters you miss show up here.'}</span>`; return; }
  box.innerHTML = `<b>YOUR PROBLEM LETTERS</b> ${w.map(x => `<span class="wk" title="missed ${Math.round(x[1] * 100)}% of ${x[2]}">${esc(x[0])}<small>${Math.round(x[1] * 100)}%</small></span>`).join('')}
   <button type="button" class="cw-small" id="cwWeakGo">PRACTICE THESE</button> <button type="button" class="cw-small" id="cwWeakReset" title="Clear the counts">RESET</button>`;
  $('cwWeakGo').addEventListener('click', () => { const sel = $('cwDrillType'); if (sel) { sel.value = 'weak'; sel.dispatchEvent(new Event('change')); } drillPlay(true); });
  $('cwWeakReset').addEventListener('click', () => { if (!confirm('Clear your problem-letter counts?')) return; MISS = {}; try { localStorage.removeItem('kpcCWmiss'); } catch (e) {} weakShow(); });
}
function weakGroup() {
  const w = weakList(10); if (!w.length) return null;
  const pool = []; w.forEach(x => { for (let i = 0; i < 1 + Math.round(x[1] * 8); i++) pool.push(x[0]); });
  const filler = 'ETAINOSRH'.split('');
  let s = ''; const words = rnd(1, 2);
  for (let k = 0; k < words; k++) { if (k) s += ' '; const n = rnd(3, 5); for (let i = 0; i < n; i++) s += chance(0.75) ? pick(pool) : pick(filler); }
  return s;
}

/* ================================================================ Head copy: listen without writing, then answer a question */
function headItem() {
  const nm = pick(NAMES), st = pick(['KY', 'KY', 'TN', 'OH', 'IN', 'VA', 'NC']), town = pick(TOWNS[st] || TOWNS.KY), rig = pick(RIGS), ant = pick(ANTS), wx = pick(WXS), t = rnd(30, 95), pw = pick([5, 10, 20, 50, 100]), y = rnd(2, 40);
  const F = [
    { s: `NAME HR IS ${nm}`, q: 'What is their name?', a: [nm] },
    { s: `QTH IS ${town} ${st}`, q: 'What town is their QTH?', a: [town, town + ' ' + st] },
    { s: `RIG HR IS ${rig}`, q: 'What rig are they using?', a: [rig, rig.replace(/ /g, '')] },
    { s: `ANT IS ${ant}`, q: 'What antenna?', a: [ant] },
    { s: `WX HR ${t < 34 ? wx : wx === 'SNOW' ? 'SUNNY' : wx} ES ${t}F`, q: 'What is the temperature there?', a: [String(t), t + 'F'] },
    { s: `PWR IS ${pw}W`, q: 'How many watts?', a: [String(pw), pw + 'W'] },
    { s: `BEEN A HAM ${y} YRS`, q: 'How many years licensed?', a: [String(y), y + ' YRS'] }];
  const use = F.sort(() => Math.random() - 0.5).slice(0, rnd(2, 3)), q = pick(use);
  return { text: use.map(f => f.s).join(' <BT> '), q: q.q, a: q.a.map(norm) };
}

/* ================================================================ Copy drills */
const KOCH = 'KMRSUAPTLOWI.NJEF0Y,VG5/Q9ZH38B?427C1D6X'.split('');
const drill = { item: '', gen: 0, v: null, right: 0, total: 0, streak: 0 };
function drillItem() {
  const k = S.drill;
  drill.head = null;
  if (k === 'head') { drill.head = headItem(); return drill.head.text; }
  if (k === 'weak') { const g = weakGroup(); if (g) return g; }
  if (k === 'calls') return newOp().call;
  if (k === 'exch') { const o = newOp(); const r = rst(S.prog); return pick([`${r} ${r} ${o.st} ${o.st}`, `TU UR ${r} ${o.st}`, `${o.call} ${r} ${o.st}`]); }
  if (k === 'refs') return S.prog === 'sota' ? place('sota', chance(0.6) ? 'KY' : 'TN')[0] : (chance(0.6) ? pick(PLACES.parks)[0] : 'US-' + String(rnd(1, 11000)).padStart(4, '0'));
  if (k === 'states') return pick(US_ST);
  if (k === 'nums') return String(rnd(0, 9999)) + (chance(0.5) ? ' ' + rnd(1, 599) : '');
  // koch
  const set = KOCH.slice(0, Math.max(2, Math.min(KOCH.length, S.kochLevel)));
  let s = ''; const words = rnd(1, 2);
  for (let w = 0; w < words; w++) { if (w) s += ' '; const n = rnd(2, 5); for (let i = 0; i < n; i++) s += pick(set); }
  return s;
}
async function drillPlay(newOne) {
  if (!audio()) return;
  if (newOne || !drill.item) { drill.item = drillItem(); const a = $('cwDrillIn'); if (a) { a.value = ''; a.focus({ preventScroll: true }); } const fb = $('cwDrillFb'); if (fb) fb.innerHTML = ''; }
  if (drill.v) drill.v.dispose();
  drill.v = new Voice({ call: 'drill', pitch: S.their, wpm: S.wpm, eff: S.eff, jit: 0, level: 0.9 });
  const a = $('cwDrillIn'), q = $('cwDrillQ');
  if (S.drill === 'head' && drill.head) { if (q) { q.hidden = false; q.textContent = 'Listen. Don\'t write anything down…'; } if (a) { a.placeholder = 'Wait for the question'; } }
  else if (q) { q.hidden = true; if (a) a.placeholder = 'Type what you heard'; }
  if (S.drill === 'weak' && !weakList().length) { const fb = $('cwDrillFb'); if (fb) fb.innerHTML = '<div class="dim">No problem letters yet, so here are Koch letters. Copy some drills first.</div>'; }
  setNoise(S.noise > 0.01); await drill.v.play(drill.item); setNoise(false);
  if (S.drill === 'head' && drill.head) { if (q) q.textContent = drill.head.q; if (a) { a.placeholder = 'Your answer'; a.focus({ preventScroll: true }); } }
}
function drillCheck() {
  const a = $('cwDrillIn'), fb = $('cwDrillFb'); if (!a || !drill.item) return;
  if (S.drill === 'head' && drill.head) {
    const got = norm(a.value), ok = drill.head.a.indexOf(got) >= 0;
    drill.total++; if (ok) { drill.right++; drill.streak++; } else drill.streak = 0;
    fb.innerHTML = `<div class="${ok ? 'good' : 'bad'}">${ok ? '✓ Right' : '✗ The answer was ' + esc(drill.head.a[0])}</div><div class="dim">They sent: ${esc(drill.head.text.replace(/<BT>/g, '='))}</div>`;
    const sc = $('cwDrillScore'); if (sc) sc.textContent = `${drill.right}/${drill.total} right · streak ${drill.streak}`;
    const auto = $('cwDrillAuto'); if (auto && auto.checked) setTimeout(() => drillPlay(true), ok ? 1200 : 2600);
    return;
  }
  const want = norm(drill.item), got = norm(a.value);
  drill.total++;
  const ok = want === got;
  trackCopy(want, got);
  if (ok) { drill.right++; drill.streak++; } else drill.streak = 0;
  // character-by-character view
  let view = '';
  for (let i = 0; i < want.length; i++) { const c = want[i]; view += `<span class="${got[i] === c ? 'ok' : 'miss'}">${esc(c === ' ' ? ' ' : c)}</span>`; }
  fb.innerHTML = `<div class="${ok ? 'good' : 'bad'}">${ok ? '✓ Correct' : '✗ It was'}</div><div class="cw-diff">${view}</div>${ok ? '' : `<div class="dim">You typed: ${esc(got || '(nothing)')}</div>`}`;
  const sc = $('cwDrillScore'); if (sc) sc.textContent = `${drill.right}/${drill.total} right · streak ${drill.streak}`;
  if (S.drill === 'koch' && drill.total >= 20 && drill.right / drill.total >= 0.9 && S.kochLevel < KOCH.length) {
    fb.innerHTML += `<div class="good">90% copy — ready for the next Koch character (${esc(KOCH[S.kochLevel])}).</div>`;
  }
  const auto = $('cwDrillAuto'); if (auto && auto.checked) setTimeout(() => drillPlay(true), ok ? 700 : 1800);
}

/* ================================================================ QRQ speed ladder
   COPY: we send, you type it. SEND: we show it, you key it. Every clean one speeds up; three misses ends the run.
   Your score is the fastest speed you got right. Clean signal (no noise or fading) so scores compare fairly. */
const WORDS = ['TU', '73', '5NN', 'NAME', 'QTH', 'RIG', 'ANT', 'WX', 'FB', 'OM', 'ES', 'PWR', 'QRZ', 'CQ', 'POTA', 'SOTA', 'PARK', 'AGN', 'HW', 'CPY', 'GM', 'GA', 'GE', 'RST', 'TNX', 'DE', 'UR', 'KY', 'QRP', 'QRQ', 'QSB', 'QRM', 'BK', 'SUMMIT', 'RADIO', 'KEY', 'TEST', 'HAM', 'CLUB', 'THE', 'AND', 'GOOD', 'HERE', 'THERE', 'SIGNAL', 'COPY', 'LOUD', 'NICE', 'SUNNY', 'RAIN', 'COLD', 'HOT', 'BATTERY', 'WIRE', 'VERTICAL', 'DIPOLE', 'KENTUCKY', 'TRAIL', 'LAKE', 'FOREST', 'RIVER', 'CAMP'];
const QBADGE = [[15, '🥉', 'Bronze'], [20, '🥈', 'Silver'], [25, '🥇', 'Gold'], [30, '🏆', 'Trophy'], [35, '⚡', 'QRQ'], [40, '🚀', 'Rocket']];
const qrq = { on: false, kind: 'copy', what: 'calls', wpm: 15, start: 15, top: 0, lives: 3, pts: 0, n: 0, item: '', rep: false, v: null, busy: false, t: 0 };
let QPB = {}; try { QPB = JSON.parse(localStorage.getItem('kpcQRQ') || '{}') || {}; } catch (e) { QPB = {}; }
function qrqItem() {
  if (qrq.weekly) return qrq.list[qrq.n % qrq.list.length];
  const w = qrq.what === 'mixed' ? pick(['calls', 'calls', 'refs', 'words']) : qrq.what;
  if (w === 'calls') return newOp().call;
  if (w === 'refs') return chance(0.7) ? 'US-' + String(rnd(1, 11000)).padStart(4, '0') : pick(PLACES.parks)[0];
  return chance(0.5) ? pick(WORDS) : pick(WORDS) + ' ' + pick(WORDS);
}
function qrqShow() {
  const set = (id, v) => { const e = $(id); if (e) e.textContent = v; };
  set('qrqWpm', qrq.on || qrq.n ? qrq.wpm + ' WPM' : '–');
  set('qrqTop', qrq.top ? qrq.top + ' WPM' : '–');
  set('qrqLives', qrq.on || qrq.n ? '❤'.repeat(Math.max(0, qrq.lives)) + '♡'.repeat(Math.max(0, 3 - qrq.lives)) : '❤❤❤');
  set('qrqPts', String(qrq.pts));
  const go = $('qrqGo'); if (go) { go.textContent = qrq.on ? '■ STOP' : '▶ START LADDER'; go.classList.toggle('stop', qrq.on); }
  document.querySelectorAll('[data-q]').forEach(e => { e.hidden = e.dataset.q !== qrq.kind; });
  const app = $('cwApp'); if (app) app.dataset.qrq = qrq.kind;
  const kn = $('qrqKeyNote'); if (kn) kn.hidden = !(qrq.kind === 'send' && S.input === 'keyboard');
  qrqBest();
}
function qrqBest() {
  const box = $('qrqPB'); if (!box) return;
  const c = QPB.copy || {}, s = QPB.send || {}, best = Math.max(c.wpm || 0, s.wpm || 0);
  const badges = QBADGE.map(b => `<span class="qb${best >= b[0] ? ' on' : ''}" title="${b[2]}: ${b[0]} WPM">${b[1]}<small>${b[0]}</small></span>`).join('');
  box.innerHTML = `<div class="qpb"><b>YOUR BEST</b> Copy: ${c.wpm ? c.wpm + ' WPM' : '–'} · Send: ${s.wpm ? s.wpm + ' WPM' : '–'}</div><div class="qbadges">${badges}</div>` +
    (best ? `<button type="button" class="cw-small" id="qrqShare">📣 SHARE MY SCORE</button><span class="dim" id="qrqShared"></span>` : '<div class="dim">Badges light up at 15, 20, 25, 30, 35 and 40 WPM.</div>');
  const sh = $('qrqShare'); if (sh) sh.addEventListener('click', qrqShare);
}
async function qrqShare() {
  const c = QPB.copy || {}, s = QPB.send || {}, me = myCall();
  const parts = []; if (c.wpm) parts.push(`copied ${c.wpm} WPM`); if (s.wpm) parts.push(`sent ${s.wpm} WPM`);
  const txt = `${me || 'I'} ${parts.join(' and ')} on the KPC QRQ Speed Ladder ⚡ How fast can you go? https://kentuckyportableclub.github.io/KPC-Links/kpc-cw.html#qrq`;
  const out = $('qrqShared');
  try { if (navigator.share) { await navigator.share({ text: txt }); return; } await navigator.clipboard.writeText(txt); if (out) out.textContent = ' Copied. Paste it in Discord or Facebook.'; }
  catch (e) { if (out) out.textContent = ' ' + txt; }
}
function qrqStart() {
  if (qrq.on) { qrqEnd(true); return; }
  if (!audio()) return;
  qrq.kind = (document.querySelector('input[name=qrqKind]:checked') || {}).value || 'copy';
  qrq.what = ($('qrqWhat') || {}).value || 'calls';
  qrq.start = +(($('qrqStart') || {}).value || 15);
  qrq.weekly = false;
  if (qrq.kind === 'send' && S.input === 'keyboard') { qrqShow(); const f = $('qrqFb'); if (f) f.innerHTML = '<div class="bad">Pick Straight key or Paddles under Your Key first.</div>'; return; }
  Object.assign(qrq, { on: true, wpm: qrq.start, top: 0, lives: 3, pts: 0, n: 0, item: '', rep: false });
  try { localStorage.setItem('kpcQRQset', JSON.stringify({ kind: qrq.kind, what: qrq.what, start: qrq.start })); } catch (e) {}
  if (qrq.kind === 'send') dec.reset(1200 / qrq.wpm, S.input === 'straight');
  $('qrqFb').innerHTML = ''; qrqShow(); qrqNext();
}
async function qrqNext() {
  if (!qrq.on) return;
  qrq.item = qrqItem(); qrq.rep = false; qrq.n++; qrq.t = performance.now();
  qrqShow();
  if (qrq.kind === 'copy') {
    const a = $('qrqIn'); if (a) { a.value = ''; a.focus({ preventScroll: true }); }
    await qrqPlay();
  } else {
    if (S.input === 'iambic') dec.reset(1200 / qrq.wpm, false); else dec.unit = 1200 / qrq.wpm;
    const t = $('qrqTarget'); if (t) t.innerHTML = `<small>SEND THIS AT ${qrq.wpm} WPM</small>${esc(qrq.item)}`;
  }
}
async function qrqPlay() {
  if (!qrq.item || !audio()) return;
  if (qrq.v) qrq.v.dispose();
  qrq.v = new Voice({ call: 'qrq', pitch: S.their, wpm: qrq.wpm, eff: qrq.wpm, jit: 0, level: 0.9, noQsb: true });
  qrq.busy = true; try { await qrq.v.play(qrq.item); } finally { qrq.busy = false; }
}
function qrqRepeat() { if (!qrq.on || !qrq.item) return; if (qrq.kind === 'copy') qrq.rep = true; qrqPlay(); }
function qrqDiff(want, got) { let v = ''; for (let i = 0; i < want.length; i++) { const c = want[i]; v += `<span class="${got[i] === c ? 'ok' : 'miss'}">${esc(c)}</span>`; } return `<div class="cw-diff">${v}</div>`; }
function qrqResult(ok, msg, noSpeedUp) {
  const fb = $('qrqFb'), at = qrq.wpm;
  if (ok) {
    qrq.top = Math.max(qrq.top, at);
    qrq.pts += Math.max(1, Math.round(at * norm(qrq.item).replace(/ /g, '').length / 5));
    if (!noSpeedUp) qrq.wpm = Math.min(60, at + (at < 20 ? 2 : 1));
  } else { qrq.lives--; qrq.wpm = Math.max(5, Math.min(at, Math.max(qrq.start, at - 2))); }
  if (fb) fb.innerHTML = msg;
  qrqShow();
  if (qrq.lives <= 0) { qrqEnd(false); return; }
  setTimeout(qrqNext, ok ? 700 : 1600);
}
function qrqCheck() {
  if (!qrq.on || qrq.kind !== 'copy' || !qrq.item) return;
  const a = $('qrqIn'); const want = norm(qrq.item), got = norm(a ? a.value : '');
  if (!got) return;
  const ok = want === got, at = qrq.wpm;
  trackCopy(want, got);
  qrqResult(ok, ok ? `<div class="good">✓ ${esc(want)} at ${at} WPM${qrq.rep ? ' (replayed, so no speed-up)' : ''}</div>`
    : `<div class="bad">✗ It was ${esc(want)}</div>${qrqDiff(want, got)}<div class="dim">You typed: ${esc(got)}</div>`, qrq.rep);
}
function qrqSent(text, how) {
  if (!qrq.on || qrq.kind !== 'send' || !qrq.item) return;
  if (how === 'type') { $('qrqFb').innerHTML = '<div class="bad">Use your key or paddles for the send ladder.</div>'; return; }
  const want = norm(qrq.item), got = norm(text), at = qrq.wpm;
  const meas = S.input === 'straight' ? Math.round(1200 / dec.unit) : at;
  if (want !== got) { qrqResult(false, `<div class="bad">✗ Decoded "${esc(got || '?')}"</div>${qrqDiff(want, got)}<div class="dim">Wanted ${esc(want)}</div>`); return; }
  if (S.input === 'straight' && meas < at - 1) { // clean but slow: no strike, try another at the same speed
    $('qrqFb').innerHTML = `<div class="dim">Clean copy, but you sent about ${meas} WPM. Aim for ${at}.</div>`; setTimeout(qrqNext, 1200); return;
  }
  qrqResult(true, `<div class="good">✓ Clean at ${S.input === 'straight' ? 'about ' + meas : at} WPM</div>`);
}
function qrqEnd(stopped) {
  if (qrq.weekly && qrq.n) weeklySave();
  qrq.on = false; if (qrq.v) { qrq.v.dispose(); qrq.v = null; }
  const fb = $('qrqFb'), k = qrq.kind, pb = QPB[k] || {};
  let line = '';
  if (qrq.top) {
    const isPB = qrq.top > (pb.wpm || 0);
    if (isPB) { QPB[k] = { wpm: qrq.top, pts: qrq.pts, what: qrq.what, date: new Date().toISOString().slice(0, 10) }; try { localStorage.setItem('kpcQRQ', JSON.stringify(QPB)); } catch (e) {} }
    const b = QBADGE.filter(x => qrq.top >= x[0]).pop();
    line = `<div class="qrq-end"><b>${qrq.top} WPM</b> ${k === 'copy' ? 'copied' : 'sent'} · ${qrq.pts} points${b ? ' · ' + b[1] + ' ' + b[2] : ''}${isPB ? '<br>🎉 New personal best!' : ''}</div>`;
  } else if (!stopped) line = '<div class="qrq-end">No clean ones that run. Try a slower start speed.</div>';
  if (fb) fb.innerHTML = (stopped ? '' : '<div class="bad">Three misses. Run over.</div>') + line + (fb && stopped ? fb.innerHTML : '');
  const t = $('qrqTarget'); if (t) t.innerHTML = '';
  qrqShow();
}
/* This week's KPC challenge: the same 60 calls, park numbers and words for everyone this week (picked from the week number),
   copy ladder starting at 15 WPM. Score = points. */
function isoWeek(d) { const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate())); const day = t.getUTCDay() || 7; t.setUTCDate(t.getUTCDate() + 4 - day); const y = t.getUTCFullYear(); return [y, Math.ceil(((t - Date.UTC(y, 0, 1)) / 86400000 + 1) / 7)]; }
function seeded(seed, fn) { const keep = Math.random; let a = seed >>> 0; Math.random = () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; try { return fn(); } finally { Math.random = keep; } }
let WK = {}; try { WK = JSON.parse(localStorage.getItem('kpcWeekly') || '{}') || {}; } catch (e) { WK = {}; }
const weekId = () => { const w = isoWeek(new Date()); return w[0] + '-W' + String(w[1]).padStart(2, '0'); };
function weeklyStart() {
  if (qrq.on) qrqEnd(true);
  if (!audio()) return;
  const id = weekId(), seed = id.split('').reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
  qrq.list = seeded(seed, () => { const out = []; for (let i = 0; i < 60; i++) { const r2 = Math.random(); out.push(r2 < 0.6 ? newOp().call : r2 < 0.8 ? 'US-' + String(rnd(1, 11000)).padStart(4, '0') : pick(WORDS)); } return out; });
  const k = document.querySelector('input[name=qrqKind][value=copy]'); if (k) k.checked = true;
  Object.assign(qrq, { kind: 'copy', weekly: true, start: 15, on: true, wpm: 15, top: 0, lives: 3, pts: 0, n: 0, item: '', rep: false });
  $('qrqFb').innerHTML = `<div class="dim">🏆 Week ${id.slice(-2)} challenge: same calls for everyone. Go!</div>`; qrqShow(); qrqNext();
}
function weeklySave() {
  const id = weekId(), b = WK[id];
  if (!b || qrq.pts > b.pts) { WK[id] = { pts: qrq.pts, wpm: qrq.top, date: new Date().toISOString().slice(0, 10) }; try { localStorage.setItem('kpcWeekly', JSON.stringify(WK)); } catch (e) {} }
  weeklyShow();
}
function weeklyShow() {
  const box = $('wkInfo'); if (!box) return;
  const id = weekId(), b = WK[id];
  box.innerHTML = `<b>THIS WEEK'S KPC CHALLENGE</b> <span class="dim">Week ${id.slice(-2)} · same calls for everyone · copy ladder from 15 WPM · new set every Monday</span><br>` +
    (b ? `Your best this week: <b>${b.pts} points</b> (top ${b.wpm} WPM) <button type="button" class="cw-small" id="wkShare">📣 SHARE</button><a class="cw-small" id="wkSubmit" hidden target="_blank" rel="noopener">🏆 SUBMIT MY SCORE</a><span class="dim" id="wkShared"></span>` : '<span class="dim">No score yet this week.</span>');
  if (b && window.KPCCWBoard) KPCCWBoard.ready.then(() => { const a = $('wkSubmit'), u = KPCCWBoard.link('copy', id, b.pts, b.wpm, S.call); if (a && u) { a.href = u; a.hidden = false; } });
  const sh = $('wkShare'); if (sh) sh.addEventListener('click', async () => {
    const txt = `${myCall() || 'I'} scored ${b.pts} points (copied up to ${b.wpm} WPM) on the KPC CW Challenge, week ${id.slice(-2)} 🏆 Same calls for everyone: https://kentuckyportableclub.github.io/KPC-Links/kpc-cw.html#qrq`;
    const out = $('wkShared');
    try { if (navigator.share) { await navigator.share({ text: txt }); return; } await navigator.clipboard.writeText(txt); if (out) out.textContent = ' Copied. Paste it in the KPC Discord.'; } catch (e) { if (out) out.textContent = ' ' + txt; }
  });
}
function qrqInit() {
  if (!$('qrqGo')) return;
  let st = {}; try { st = JSON.parse(localStorage.getItem('kpcQRQset') || '{}') || {}; } catch (e) {}
  const kr = document.querySelector(`input[name=qrqKind][value=${st.kind === 'send' ? 'send' : 'copy'}]`); if (kr) kr.checked = true;
  qrq.kind = kr ? kr.value : 'copy';
  if (st.what && $('qrqWhat')) $('qrqWhat').value = st.what;
  if ($('qrqStart')) $('qrqStart').value = String(st.start || (S.wpm <= 12 ? 10 : S.wpm <= 17 ? 15 : S.wpm <= 22 ? 20 : 25));
  document.querySelectorAll('input[name=qrqKind]').forEach(rr => rr.addEventListener('change', () => { if (qrq.on) qrqEnd(true); qrq.kind = rr.value; qrqShow(); }));
  $('qrqGo').addEventListener('click', qrqStart);
  if ($('wkGo')) $('wkGo').addEventListener('click', weeklyStart); weeklyShow();
  $('qrqRep').addEventListener('click', qrqRepeat);
  $('qrqOk').addEventListener('click', qrqCheck);
  $('qrqIn').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); qrqCheck(); } });
  qrqShow();
}

/* ================================================================ Wiring */
function typedSend() {
  const i = $('cwType'); if (!i) return;
  const text = i.value.trim(); if (!text) return;
  i.value = '';
  if (!audio()) return;
  // play it on your sidetone at your speed, then hand it to the other station
  const tl = timeline(text, S.wpm, S.eff, 0), t0 = AC.currentTime + 0.03, g = myG.gain;
  g.cancelScheduledValues(t0);
  tl.marks.forEach(m => { g.setTargetAtTime(1, t0 + m[0], RAMP); g.setTargetAtTime(0, t0 + m[1], RAMP); });
  ui.lamp(true); setTimeout(() => ui.lamp(false), tl.total * 1000);
  setTimeout(() => transmit(text.toUpperCase(), 'type'), tl.total * 1000 + 250);
}

function bindKeys() {
  const inField = e => /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || e.target.isContentEditable;
  const role = e => {
    if (S.input === 'straight') return (e.code === 'Space' || e.code === 'ControlLeft' || e.code === 'ControlRight' || e.key === '\\') ? 'key' : null;
    if (S.input === 'iambic') {
      if (e.code === 'ControlLeft' || e.code === 'BracketLeft' || e.code === 'KeyZ' || e.code === 'Period') return '.';
      if (e.code === 'ControlRight' || e.code === 'BracketRight' || e.code === 'KeyX' || e.code === 'Slash') return '-';
    }
    return null;
  };
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { stop(); return; }
    if (inField(e) || e.metaKey || e.altKey) return;
    const r = role(e); if (!r) return;
    e.preventDefault(); if (e.repeat) return; audio();
    if (r === 'key') keyDown(); else paddle(r, true);
  });
  document.addEventListener('keyup', e => {
    const r = role(e); if (!r) return;
    if (inField(e) && !key.down && !ik.busy) return;
    e.preventDefault();
    if (r === 'key') keyUp(); else paddle(r, false);
  });
  window.addEventListener('blur', releaseAll);
  document.addEventListener('visibilitychange', () => { if (document.hidden) releaseAll(); });
  // touch / mouse keys
  const hold = (el, on, off) => {
    if (!el) return;
    el.addEventListener('pointerdown', e => { e.preventDefault(); audio(); try { el.setPointerCapture(e.pointerId); } catch (x) {} on(); });
    ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => el.addEventListener(t, e => { e.preventDefault(); off(); }));
    el.addEventListener('contextmenu', e => e.preventDefault());
  };
  hold($('cwStraight'), keyDown, keyUp);
  hold($('cwDit'), () => paddle('.', true), () => paddle('.', false));
  hold($('cwDah'), () => paddle('-', true), () => paddle('-', false));
  // Mouse paddle (computer): left button = dit, right button = dah, both = squeeze. With a straight key, any button keys.
  // mousedown/mouseup fire for each button separately, so squeezing both works.
  const mp = $('cwMouse');
  if (mp) {
    const down = new Set();
    const act = (btn, on) => {
      if (S.input === 'straight') { if (on) keyDown(); else if (!down.size) keyUp(); return; }
      if (S.input === 'iambic') paddle(btn === 2 ? '-' : '.', on);
    };
    mp.addEventListener('mousedown', e => { if (e.button !== 0 && e.button !== 2) return; e.preventDefault(); audio(); down.add(e.button); mp.classList.add('down'); act(e.button, true); });
    document.addEventListener('mouseup', e => { if (!down.has(e.button)) return; down.delete(e.button); if (!down.size) mp.classList.remove('down'); act(e.button, false); });
    mp.addEventListener('contextmenu', e => e.preventDefault());
    window.addEventListener('blur', () => { down.clear(); mp.classList.remove('down'); });
  }
}

async function midi() {
  const b = $('cwMidi');
  if (!navigator.requestMIDIAccess) { if (b) b.textContent = 'USB/MIDI keys need Chrome or Edge on a computer'; return; }
  try {
    const acc = await navigator.requestMIDIAccess();
    let n = 0;
    const hook = inp => {
      n++;
      inp.onmidimessage = ev => {
        const [st, note, vel] = ev.data; const cmd = st >> 4; if (cmd !== 8 && cmd !== 9) return;
        const on = cmd === 9 && vel > 0; audio();
        switch (note % 12) { // Vail adapter: C = straight key, C# = dit, D = dah
          case 0: on ? keyDown() : keyUp(); break;
          case 1: paddle('.', on); break;
          case 2: paddle('-', on); break;
        }
      };
    };
    acc.inputs.forEach(hook);
    acc.onstatechange = e => { if (e.port.type === 'input' && e.port.state === 'connected') hook(e.port); };
    if (b) b.textContent = n ? `✓ ${n} MIDI device${n > 1 ? 's' : ''} connected` : 'No MIDI key found — plug it in and try again';
  } catch (e) { if (b) b.textContent = 'MIDI permission was blocked'; }
}

function setMode(m) {
  stop(true); if (qrq.on) qrqEnd(true); if (game.on) gameStop(); if (gt.on) gtStop(''); if (ln.v) { ln.v.dispose(); ln.v = null; } if (keyer.v) { keyer.v.dispose(); keyer.v = null; keyer.i = -1; } MODE = m;
  const app = $('cwApp'); if (app) app.dataset.mode = m;
  document.querySelectorAll('.cw-tab').forEach(t => t.setAttribute('aria-selected', String(t.dataset.mode === m)));
  document.querySelectorAll('[data-show]').forEach(el => { el.hidden = el.dataset.show.split(' ').indexOf(m) < 0; });
  session.qsos = []; session.agn = 0; const tb = $('cwLog'); if (tb) tb.innerHTML = ''; ui.stats();
  const band = $('cwBand'); if (band) band.innerHTML = '';
  const intro = {
    hunt: `You're the ${S.prog === 'sota' ? 'chaser' : 'hunter'}. Press START, wait for the CQ, then send your call once.`,
    act: `You're the activator. Press START, then call CQ ${progWord()} with your call. Answer the stations that come back.`,
    free: 'Send anything — it decodes as you go. Use it to check your timing.',
    drill: 'Press PLAY, type what you heard, press Enter.',
    qrq: '',
    games: '',
    learn: '',
    gaunt: '',
    keyer: '',
    sprint: 'Sprint: pick the format and length, press START, call CQ and work as many as you can before the clock runs out.',
    chat: 'Ragchew: press START. Answer the CQ, then trade name, QTH, rig, antenna and weather. Send AGN? to hear an over again, or QRS to slow them down.',
    listen: ''
  }[m];
  ui.status(intro || ''); ui.hint('');
  try { localStorage.setItem('kpcCWmode', m); } catch (e) {}
  document.dispatchEvent(new CustomEvent('kpccw:mode', { detail: m }));
  if (m === 'learn' && $('lnBody')) learnGo('meet');
}
function setInput(v) {
  S.input = v; save(); releaseAll();
  document.querySelectorAll('[data-input]').forEach(el => { el.hidden = el.dataset.input.split(' ').indexOf(v) < 0; });
  dec.reset(1200 / S.wpm, v === 'straight');
  const r = document.querySelector(`input[name=cwInput][value=${v}]`); if (r) r.checked = true;
  if ($('qrqGo')) qrqShow();
  padLabels();
}

function padLabels() {
  const d = $('cwDit'), h = $('cwDah'), c = $('cwSwap'), b = $('cwSwapBtn');
  if (d) d.innerHTML = (S.swap ? 'DAH' : 'DIT') + '<small>left paddle</small>';
  if (h) h.innerHTML = (S.swap ? 'DIT' : 'DAH') + '<small>right paddle</small>';
  if (c) c.checked = !!S.swap;
  if (b) b.innerHTML = '⇄ SWAP PADDLES' + (S.swap ? ' <small>(swapped: left = dah)</small>' : '');
  const m = $('cwMouseL'); if (m) m.textContent = S.input === 'straight' ? 'Hold any mouse button to key' : (S.swap ? 'Left click = DAH · Right click = DIT' : 'Left click = DIT · Right click = DAH');
}
function bindSettings() {
  const FADE = ['Off', 'Light', 'Moderate', 'Deep', 'Deep & fast'];
  const pileTxt = v => v === 0 ? 'None: one station at a time' : v === 1 ? '1 other station' : v + ' stations calling' + (v >= 8 ? ' (big pileup)' : '');
  const FMT = {
    wpm: v => v + ' WPM', eff: v => v >= S.wpm ? 'Off (normal spacing)' : v + ' WPM overall', pitch: v => v + ' Hz', their: v => v + ' Hz',
    vol: v => Math.round(v * 100) + '%', noise: v => v < 0.01 ? 'Off' : Math.round(v * 100) + '%', pileN: pileTxt, fade: v => FADE[v] || v, over: v => v.toFixed(1) + ' s'
  };
  const UI = { vol: v => Math.round(v * 100), noise: v => Math.round(v * 100), over: v => Math.round(v * 10) };
  const TOS = { vol: v => v / 100, noise: v => v / 100, over: v => v / 10 };
  const label = k => { const o = $(IDS[k] + 'V'); if (o) o.textContent = FMT[k](S[k]); };
  const IDS = { wpm: 'cwWpm', eff: 'cwEff', pitch: 'cwPitch', their: 'cwTheir', vol: 'cwVol', noise: 'cwNoise', pileN: 'cwPile', fade: 'cwFade', over: 'cwOver' };
  Object.keys(IDS).forEach(k => {
    const el = $(IDS[k]); if (!el) return;
    el.value = UI[k] ? UI[k](S[k]) : S[k]; label(k);
    el.addEventListener('input', () => {
      S[k] = TOS[k] ? TOS[k](+el.value) : +el.value;
      if ((k === 'wpm' || k === 'eff') && S.eff > S.wpm) { S.eff = S.wpm; const e = $('cwEff'); if (e) e.value = S.eff; }
      label(k); if (k === 'wpm') label('eff');
      save(); applyAudio();
      if (k === 'fade') VOICES.forEach(v => v.setQsb());
      if (k === 'pileN') { const q = $('cwPileQ'); if (q) q.textContent = S.pileN; const qq = $('cwPile'); if (qq && +qq.value !== S.pileN) qq.value = S.pileN; }
      if (k === 'wpm' && S.input !== 'straight') dec.reset(1200 / S.wpm, false);
    });
  });
  const txt = (id, k, up) => { const el = $(id); if (!el) return; el.value = S[k] || ''; el.addEventListener('input', () => { S[k] = up ? el.value.toUpperCase().replace(/\s/g, '') : el.value; if (up) el.value = S[k]; el.classList.remove('need'); save(); }); };
  txt('cwCall', 'call', true); txt('cwRef', 'ref', true); txt('cwName', 'name', true); txt('cwQth', 'qth'); txt('cwNr', 'nr', true);
  const sel = (id, k, cb) => { const el = $(id); if (!el) return; el.value = S[k]; el.addEventListener('change', () => { S[k] = el.value; save(); cb && cb(); }); };
  sel('cwState', 'st'); sel('cwBandCond', 'bandc'); sel('spFmt', 'spFmt', spBest); sel('spMin', 'spMin', () => { S.spMin = +S.spMin; save(); spBest(); }); sel('cwShow', 'show'); sel('cwIambic', 'iambic'); sel('cwDrillType', 'drill', () => { drill.item = ''; drill.head = null; const q = $('cwDrillQ'); if (q) q.hidden = true; $('cwKochRow').hidden = S.drill !== 'koch'; });
  sel('cwProg', 'prog', () => { setMode(MODE); document.querySelectorAll('.cw-prog').forEach(e => { e.textContent = progWord(); }); });
  const chk = (id, k, cb) => { const el = $(id); if (!el) return; el.checked = !!S[k]; el.addEventListener('change', () => { S[k] = el.checked; save(); cb && cb(); }); };
  // quick pileup − / + next to START
  const setPile = v => { const el = $('cwPile'); if (!el) return; el.value = Math.max(0, Math.min(12, v)); el.dispatchEvent(new Event('input')); };
  if ($('cwPileMinus')) { $('cwPileMinus').addEventListener('click', () => setPile(S.pileN - 1)); $('cwPilePlus').addEventListener('click', () => setPile(S.pileN + 1)); $('cwPileQ').textContent = S.pileN; } chk('cwHints', 'hints', () => ui.hint($('cwHint').textContent)); chk('cwSwap', 'swap', padLabels); chk('cwMatch', 'match'); chk('cwWelcome', 'welcome');
  const koch = $('cwKoch'); if (koch) { const f = () => { S.kochLevel = +koch.value; $('cwKochV').textContent = `${S.kochLevel} characters: ${KOCH.slice(0, S.kochLevel).join(' ')}`; save(); }; koch.value = S.kochLevel; koch.addEventListener('input', f); f(); }
  if ($('cwKochRow')) $('cwKochRow').hidden = S.drill !== 'koch';
  document.querySelectorAll('input[name=cwInput]').forEach(r => r.addEventListener('change', () => setInput(r.value)));
  document.querySelectorAll('.cw-prog').forEach(e => { e.textContent = progWord(); });
}

function showLat() {
  const el = $('cwLat'); if (!el || !AC) return;
  setTimeout(() => { const ms = latencyMs(); if (ms == null) return;
    el.textContent = `Sound delay on this device: about ${ms} ms${ms > 60 ? ' (high)' : ''}. Bluetooth headphones and speakers add 100–300 ms more, so use wired headphones or the device speaker for keying.`; }, 300);
}
function init() {
  if (!$('cwApp')) return;
  bindSettings(); bindKeys();
  setInput(S.input);
  document.querySelectorAll('.cw-tab').forEach(t => t.addEventListener('click', () => setMode(t.dataset.mode)));
  let m = 'hunt'; try { m = localStorage.getItem('kpcCWmode') || 'hunt'; } catch (e) {}
  const hm = (location.hash.match(/#(hunt|act|drill|free|listen|qrq|chat|sprint|games|keyer|gaunt|learn)\b/) || [])[1]; if (hm) m = hm;
  setMode(m);
  $('cwGo').addEventListener('click', () => { if (session.on) stop(); else start(); });
  $('cwOverBtn').addEventListener('click', () => dec.flush());
  document.addEventListener('keydown', e => { if (e.key === 'Enter' && !/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(e.target.tagName) && (S.input === 'straight' || S.input === 'iambic') && (dec.text || dec.code)) { e.preventDefault(); dec.flush(); } });
  // start the sound engine on the first tap or key so the very first dit isn't late
  const warm = () => { audio(); showLat(); };
  $('cwApp').addEventListener('pointerdown', warm, { once: true }); document.addEventListener('keydown', warm, { once: true });
  document.addEventListener('visibilitychange', () => { if (!document.hidden && AC && AC.state === 'suspended') AC.resume(); });
  $('cwClear').addEventListener('click', () => { $('cwBand').innerHTML = ''; });
  const ty = $('cwType'); ty.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); typedSend(); } });
  $('cwTypeSend').addEventListener('click', typedSend);
  $('cwTest').addEventListener('click', async () => { audio(); showLat(); const v = new Voice({ call: 'test', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9 }); await v.play('VVV'); v.dispose(); });
  $('cwMidi').addEventListener('click', midi);
  $('cwDrillPlay').addEventListener('click', () => drillPlay(true));
  $('cwDrillAgain').addEventListener('click', () => drillPlay(false));
  $('cwDrillIn').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); drillCheck(); } });
  $('cwDrillOk').addEventListener('click', drillCheck);
  document.querySelectorAll('[data-say]').forEach(b => b.addEventListener('click', () => { audio(); const v = new Voice({ call: 'ex', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9 }); v.play(b.dataset.say).then(() => v.dispose()); }));
  const sb = $('cwSwapBtn'); if (sb) sb.addEventListener('click', () => { S.swap = !S.swap; save(); releaseAll(); padLabels(); });
  padLabels(); qrqInit(); weakShow(); spBest(); kInit();
  if ($('gtGo')) { $('gtGo').addEventListener('click', gtStart); $('gtAgn').addEventListener('click', gtAgn); $('gtOk').addEventListener('click', () => gtJudge(false)); $('gtIn').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); gtJudge(false); } }); gtShow(); }
  if ($('gmGo')) {
    $('gmGo').addEventListener('click', gameStart);
    document.querySelectorAll('input[name=gmKind]').forEach(x => x.addEventListener('change', () => { if (game.on) gameStop(); const f = $('gmField'); if (f) f.innerHTML = ''; gameShow(); }));
    const ty = $('gmType'); if (ty) ty.addEventListener('input', () => { const v = ty.value.toUpperCase(); ty.value = ''; for (const c of v) if (/[A-Z0-9]/.test(c)) gameChar(c); });
    gameShow();
  }
  fistMeter(); ui.stats();
}

// small hooks for testing / other pages
window.KPCCW = { timeline, charsOf, callMatch, toks, findRST, findState, findRef, lev, newOp, usCall, decode: c => DECODE[c], S, dec, transmit, session, setMode, start, stop, paddle, keyDown, keyUp, releaseAll, drill, drillItem, garble, qrq, qrqStart, qrqCheck, qrqSent, qrqEnd, waiting: () => !!waiter, gt, gtJudge, gtStart, ln, LC: () => LC, LSTEPS: LSF, trackCopy, MISS: () => MISS };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
