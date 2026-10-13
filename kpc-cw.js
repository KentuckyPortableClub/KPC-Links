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
  wpm: 18, eff: 18, pitch: 650, their: 600, vol: 0.7, noise: 0.12, qsb: true,
  input: 'keyboard', iambic: 'B', swap: false, show: 'after', hints: true, pile: 2,
  over: 1.6, match: false, kochLevel: 2, drill: 'calls'
};
let S = Object.assign({}, DEF);
try { Object.assign(S, JSON.parse(localStorage.getItem('kpcCW') || '{}')); } catch (e) {}
function save() { try { localStorage.setItem('kpcCW', JSON.stringify(S)); } catch (e) {} }

/* ================================================================ Audio */
let AC = null, master = null, myG = null, myOsc = null, noiseG = null, noiseF = null;
function audio() {
  if (!AC) {
    const C = window.AudioContext || window.webkitAudioContext;
    if (!C) return null;
    AC = new C();
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
  if (S.qsb) { // slow fading
    this.lfo = AC.createOscillator(); this.lfo.frequency.value = 0.05 + Math.random() * 0.15;
    const depth = AC.createGain(); depth.gain.value = this.level * (0.25 + Math.random() * 0.3);
    this.fade.gain.value = this.level * 0.75;
    this.lfo.connect(depth); depth.connect(this.fade.gain); this.lfo.start();
  }
  this.osc.start(); VOICES.add(this);
}
Voice.prototype.play = function (text) {
  this.cancel();
  if (!AC) return Promise.resolve();
  const tl = timeline(text, this.wpm, this.eff, this.jit), t0 = AC.currentTime + 0.06, g = this.env.gain;
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
  down(t) { this.clear(); this.downAt = t; },
  up(t) {
    const d = t - this.downAt; if (d < 8) return;
    if (!this.adapt) this.unit = 1200 / S.wpm;   // paddles: the keyer's own speed
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
const key = { down: false };
function keyDown() { if (key.down) return; key.down = true; sidetone(true); dec.down(performance.now()); ui.lamp(true); }
function keyUp() { if (!key.down) return; key.down = false; sidetone(false); dec.up(performance.now()); ui.lamp(false); }

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
  const u = 1200 / S.wpm, d = el === '.' ? u : 3 * u;
  ik.busy = true; ik.last = el;
  keyDown();
  ik.timer = setTimeout(() => { keyUp(); ik.timer = setTimeout(nextElement, u); }, d);
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
const myCall = () => (S.call || '').toUpperCase().trim();
const progWord = () => S.prog === 'sota' ? 'SOTA' : 'POTA';
const goal = () => S.prog === 'sota' ? 4 : 10;

function stop(silent) {
  GEN++; session.on = false;
  if (waiter) { const w = waiter; waiter = null; clearTimeout(waitTimer); w(null); }
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
  if (MODE === 'hunt') hunterLoop(gen).catch(e => console.error(e));
  else if (MODE === 'act') activatorLoop(gen).catch(e => console.error(e));
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
    const n = S.pile === 0 ? 0 : rnd(Math.max(0, S.pile - 2), S.pile + (S.pile >= 3 ? 2 : 0));
    pileOps = []; const used = new Set([me, act.call]);
    for (let i = 0; i < n; i++) { const o = newOp(used); used.add(o.call); pileOps.push(Object.assign(o, { v: voice(o.call) })); }
    pileOps.forEach(o => { setTimeout(() => { if (gen === GEN) { busyThem++; o.v.play(o.call + (chance(0.35) ? ' ' + o.call : '')).then(() => busyThem--); } }, rnd(150, 1100)); });
    const r = await you(6500 + n * 600);
    if (gen !== GEN) return;
    const ts = toks(r);
    const m = r ? callMatch(ts, me) : null;
    const p2p = has(ts, 'P2P', 'S2S');
    const won = m === 'exact' && (pileOps.length === 0 || chance(p2p ? 0.95 : 0.72));
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
    const want = [1, 2, 3, 5, 7][S.pile] || 2; const n = Math.max(0, rnd(Math.max(1, want - 1), want) - callers.length);
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
  const steady = Math.round(100 - Math.min(60, (sd(dits) + sd(dahs)) * 100));
  const rc = Math.abs(ratio - 3) < 0.45 ? 'good' : Math.abs(ratio - 3) < 0.9 ? 'ok' : 'bad';
  e.innerHTML = `<div><b>${wpm}</b><span>WPM (from your dits)</span></div><div class="${rc}"><b>${ratio.toFixed(1)} : 1</b><span>dah : dit (aim for 3)</span></div><div class="${steady > 80 ? 'good' : steady > 65 ? 'ok' : 'bad'}"><b>${steady}%</b><span>steadiness</span></div>`;
}

/* ================================================================ Copy drills */
const KOCH = 'KMRSUAPTLOWI.NJEF0Y,VG5/Q9ZH38B?427C1D6X'.split('');
const drill = { item: '', gen: 0, v: null, right: 0, total: 0, streak: 0 };
function drillItem() {
  const k = S.drill;
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
  setNoise(S.noise > 0.01); await drill.v.play(drill.item); setNoise(false);
}
function drillCheck() {
  const a = $('cwDrillIn'), fb = $('cwDrillFb'); if (!a || !drill.item) return;
  const want = norm(drill.item), got = norm(a.value);
  drill.total++;
  const ok = want === got;
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
  stop(true); MODE = m;
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
    listen: ''
  }[m];
  ui.status(intro || ''); ui.hint('');
  try { localStorage.setItem('kpcCWmode', m); } catch (e) {}
  document.dispatchEvent(new CustomEvent('kpccw:mode', { detail: m }));
}
function setInput(v) {
  S.input = v; save(); releaseAll();
  document.querySelectorAll('[data-input]').forEach(el => { el.hidden = el.dataset.input.split(' ').indexOf(v) < 0; });
  dec.reset(1200 / S.wpm, v === 'straight');
  const r = document.querySelector(`input[name=cwInput][value=${v}]`); if (r) r.checked = true;
}

function bindSettings() {
  const PILE = ['Quiet (1 at a time)', 'Light', 'Normal', 'Busy', 'Big pileup'];
  const FMT = {
    wpm: v => v + ' WPM', eff: v => v >= S.wpm ? 'Off (normal spacing)' : v + ' WPM overall', pitch: v => v + ' Hz', their: v => v + ' Hz',
    vol: v => Math.round(v * 100) + '%', noise: v => v < 0.01 ? 'Off' : Math.round(v * 100) + '%', pile: v => PILE[v] || v, over: v => v.toFixed(1) + ' s'
  };
  const UI = { vol: v => Math.round(v * 100), noise: v => Math.round(v * 100), over: v => Math.round(v * 10) };
  const TOS = { vol: v => v / 100, noise: v => v / 100, over: v => v / 10 };
  const label = k => { const o = $(IDS[k] + 'V'); if (o) o.textContent = FMT[k](S[k]); };
  const IDS = { wpm: 'cwWpm', eff: 'cwEff', pitch: 'cwPitch', their: 'cwTheir', vol: 'cwVol', noise: 'cwNoise', pile: 'cwPile', over: 'cwOver' };
  Object.keys(IDS).forEach(k => {
    const el = $(IDS[k]); if (!el) return;
    el.value = UI[k] ? UI[k](S[k]) : S[k]; label(k);
    el.addEventListener('input', () => {
      S[k] = TOS[k] ? TOS[k](+el.value) : +el.value;
      if ((k === 'wpm' || k === 'eff') && S.eff > S.wpm) { S.eff = S.wpm; const e = $('cwEff'); if (e) e.value = S.eff; }
      label(k); if (k === 'wpm') label('eff');
      save(); applyAudio();
      if (k === 'wpm' && S.input !== 'straight') dec.reset(1200 / S.wpm, false);
    });
  });
  const txt = (id, k, up) => { const el = $(id); if (!el) return; el.value = S[k] || ''; el.addEventListener('input', () => { S[k] = up ? el.value.toUpperCase().replace(/\s/g, '') : el.value; if (up) el.value = S[k]; el.classList.remove('need'); save(); }); };
  txt('cwCall', 'call', true); txt('cwRef', 'ref', true);
  const sel = (id, k, cb) => { const el = $(id); if (!el) return; el.value = S[k]; el.addEventListener('change', () => { S[k] = el.value; save(); cb && cb(); }); };
  sel('cwState', 'st'); sel('cwShow', 'show'); sel('cwIambic', 'iambic'); sel('cwDrillType', 'drill', () => { drill.item = ''; $('cwKochRow').hidden = S.drill !== 'koch'; });
  sel('cwProg', 'prog', () => { setMode(MODE); document.querySelectorAll('.cw-prog').forEach(e => { e.textContent = progWord(); }); });
  const chk = (id, k, cb) => { const el = $(id); if (!el) return; el.checked = !!S[k]; el.addEventListener('change', () => { S[k] = el.checked; save(); cb && cb(); }); };
  chk('cwQsb', 'qsb'); chk('cwHints', 'hints', () => ui.hint($('cwHint').textContent)); chk('cwSwap', 'swap'); chk('cwMatch', 'match');
  const koch = $('cwKoch'); if (koch) { const f = () => { S.kochLevel = +koch.value; $('cwKochV').textContent = `${S.kochLevel} characters: ${KOCH.slice(0, S.kochLevel).join(' ')}`; save(); }; koch.value = S.kochLevel; koch.addEventListener('input', f); f(); }
  if ($('cwKochRow')) $('cwKochRow').hidden = S.drill !== 'koch';
  document.querySelectorAll('input[name=cwInput]').forEach(r => r.addEventListener('change', () => setInput(r.value)));
  document.querySelectorAll('.cw-prog').forEach(e => { e.textContent = progWord(); });
}

function init() {
  if (!$('cwApp')) return;
  bindSettings(); bindKeys();
  setInput(S.input);
  document.querySelectorAll('.cw-tab').forEach(t => t.addEventListener('click', () => setMode(t.dataset.mode)));
  let m = 'hunt'; try { m = localStorage.getItem('kpcCWmode') || 'hunt'; } catch (e) {}
  const hm = (location.hash.match(/#(hunt|act|drill|free|listen)\b/) || [])[1]; if (hm) m = hm;
  setMode(m);
  $('cwGo').addEventListener('click', () => { if (session.on) stop(); else start(); });
  $('cwOverBtn').addEventListener('click', () => dec.flush());
  $('cwClear').addEventListener('click', () => { $('cwBand').innerHTML = ''; });
  const ty = $('cwType'); ty.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); typedSend(); } });
  $('cwTypeSend').addEventListener('click', typedSend);
  $('cwTest').addEventListener('click', async () => { audio(); const v = new Voice({ call: 'test', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9 }); await v.play('VVV'); v.dispose(); });
  $('cwMidi').addEventListener('click', midi);
  $('cwDrillPlay').addEventListener('click', () => drillPlay(true));
  $('cwDrillAgain').addEventListener('click', () => drillPlay(false));
  $('cwDrillIn').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); drillCheck(); } });
  $('cwDrillOk').addEventListener('click', drillCheck);
  document.querySelectorAll('[data-say]').forEach(b => b.addEventListener('click', () => { audio(); const v = new Voice({ call: 'ex', pitch: S.their, wpm: S.wpm, eff: S.eff, level: 0.9 }); v.play(b.dataset.say).then(() => v.dispose()); }));
  fistMeter(); ui.stats();
}

// small hooks for testing / other pages
window.KPCCW = { timeline, charsOf, callMatch, toks, findRST, findState, findRef, lev, newOp, usCall, decode: c => DECODE[c], S, dec, transmit, session, setMode, start, stop, paddle, keyDown, keyUp, releaseAll, drill, drillItem, garble };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
