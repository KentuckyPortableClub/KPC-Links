/* KPC Voice Pileup Practice (BETA): you're the POTA activator on SSB. Stations call you (browser voices),
   you type what you hear into the log, send them a report, copy theirs, and log it. Levels grow the pileup.
   Browser voices speak one at a time, so a "pileup" here is callers stacked back to back with tail-enders. */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1)), pick = a => a[Math.floor(Math.random() * a.length)], chance = p => Math.random() < p;
const store = { get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };

const NATO = { A: 'Alpha', B: 'Bravo', C: 'Charlie', D: 'Delta', E: 'Echo', F: 'Foxtrot', G: 'Golf', H: 'Hotel', I: 'India', J: 'Juliet', K: 'Kilo', L: 'Lima', M: 'Mike', N: 'November', O: 'Oscar', P: 'Papa', Q: 'Quebec', R: 'Romeo', S: 'Sierra', T: 'Tango', U: 'Uniform', V: 'Victor', W: 'Whiskey', X: 'X-ray', Y: 'Yankee', Z: 'Zulu',
  '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '/': 'portable' };
const STN = { AL: 'Alabama', AR: 'Arkansas', AZ: 'Arizona', CA: 'California', CO: 'Colorado', CT: 'Connecticut', DE: 'Delaware', FL: 'Florida', GA: 'Georgia', IA: 'Iowa', ID: 'Idaho', IL: 'Illinois', IN: 'Indiana', KS: 'Kansas', KY: 'Kentucky', LA: 'Louisiana', MA: 'Massachusetts', MD: 'Maryland', ME: 'Maine', MI: 'Michigan', MN: 'Minnesota', MO: 'Missouri', MS: 'Mississippi', MT: 'Montana', NC: 'North Carolina', ND: 'North Dakota', NE: 'Nebraska', NH: 'New Hampshire', NJ: 'New Jersey', NM: 'New Mexico', NV: 'Nevada', NY: 'New York', OH: 'Ohio', OK: 'Oklahoma', OR: 'Oregon', PA: 'Pennsylvania', RI: 'Rhode Island', SC: 'South Carolina', SD: 'South Dakota', TN: 'Tennessee', TX: 'Texas', UT: 'Utah', VA: 'Virginia', VT: 'Vermont', WA: 'Washington', WI: 'Wisconsin', WV: 'West Virginia', WY: 'Wyoming' };
const AREA = { 1: 'CT ME MA NH RI VT', 2: 'NJ NY', 3: 'DE MD PA', 4: 'AL FL GA KY NC SC TN VA', 5: 'AR LA MS NM OK TX', 6: 'CA', 7: 'AZ ID MT NV OR UT WA WY', 8: 'MI OH WV', 9: 'IL IN WI', 0: 'CO IA KS MN MO NE ND SD' };
const ST_AREA = {}; Object.keys(AREA).forEach(n => AREA[n].split(' ').forEach(s => { ST_AREA[s] = n; }));
const NEAR = ['KY', 'KY', 'TN', 'TN', 'OH', 'OH', 'IN', 'IN', 'WV', 'VA', 'IL', 'MO', 'NC', 'GA', 'MI', 'PA', 'AL', 'TX', 'FL', 'NY', 'WI', 'CA', 'MN', 'CO', 'AZ', 'WA'];
const L = () => String.fromCharCode(65 + rnd(0, 25));
/* who you can hear depends on the band: 40 m = nearby states (some farther), 20 m / 17 m skip over the
   neighbours (the skip zone) and bring in stations 500+ miles away. Rough state centers (lat, lon). */
const CEN = { AL: [32.8, -86.8], AR: [34.9, -92.4], AZ: [34.3, -111.7], CA: [37.2, -119.5], CO: [39, -105.5], CT: [41.6, -72.7], DE: [39, -75.5], FL: [28.6, -82.4], GA: [32.7, -83.4], IA: [42.1, -93.5], ID: [44.4, -114.6], IL: [40, -89.2], IN: [39.9, -86.3], KS: [38.5, -98.4], KY: [37.5, -85.3], LA: [31.1, -92], MA: [42.3, -71.8], MD: [39, -76.8], ME: [45.4, -69.2], MI: [43.7, -84.7], MN: [46.3, -94.3], MO: [38.4, -92.5], MS: [32.7, -89.7], MT: [47, -109.6], NC: [35.6, -79.4], ND: [47.5, -100.5], NE: [41.5, -99.8], NH: [43.7, -71.6], NJ: [40.2, -74.7], NM: [34.4, -106.1], NV: [39.3, -116.6], NY: [42.9, -75.5], OH: [40.3, -82.8], OK: [35.6, -97.5], OR: [43.9, -120.6], PA: [40.9, -77.8], RI: [41.7, -71.5], SC: [33.9, -80.9], SD: [44.4, -100.2], TN: [35.9, -86.4], TX: [31.5, -99.3], UT: [39.3, -111.7], VA: [37.5, -78.8], VT: [44.1, -72.7], WA: [47.4, -120.5], WI: [44.6, -89.9], WV: [38.6, -80.6], WY: [43, -107.6] };
const HAMS = { CA: 3, TX: 2.5, FL: 2, NY: 1.8, PA: 1.4, OH: 1.4, IL: 1.3, GA: 1.2, NC: 1.2, MI: 1.2, VA: 1.1, WA: 1.1, TN: 1.1, KY: 1.1, IN: 1, AZ: 1, CO: 1, DE: 0.3, RI: 0.3, VT: 0.3, WY: 0.3, ND: 0.3, SD: 0.35, MT: 0.45, NH: 0.5, ME: 0.5, NV: 0.6, ID: 0.5, NE: 0.5 }; // roughly how many hams live there
function miles(a, b) { const A = CEN[a], B = CEN[b]; if (!A || !B) return 800; const r = Math.PI / 180, x = (B[1] - A[1]) * r * Math.cos((A[0] + B[0]) / 2 * r), y = (B[0] - A[0]) * r; return Math.sqrt(x * x + y * y) * 3959; }
function bandWeight(band, d) {
  if (String(band) === '40') return d < 700 ? 1 : d < 1200 ? 0.3 : 0.06;
  return d < 120 ? 0.04 : d < 450 ? 0.03 : d < 650 ? 0.4 : d < 2600 ? 1 : 0.5; // 20 m / 17 m
}
function pickState(band, from) {
  const home = CEN[from] ? from : 'KY', keys = Object.keys(CEN), w = keys.map(k => bandWeight(band, miles(home, k)) * (HAMS[k] || 0.8));
  let t = Math.random() * w.reduce((a, b) => a + b, 0);
  for (let i = 0; i < keys.length; i++) { t -= w[i]; if (t <= 0) return keys[i]; }
  return 'TX';
}
function newCall(st) {
  const n = ST_AREA[st], f = rnd(1, 100), p = () => pick(['K', 'W', 'N']);
  if (f <= 12) return p() + n + L() + L();
  if (f <= 45) return p() + n + L() + L() + L();
  if (f <= 58) return p() + L() + n + L() + L();
  return pick(['K', 'W', 'N']) + pick('ABCDEFGIJKMNOQ'.split('')) + n + L() + L() + L();
}
const say1 = c => c.split('').map(ch => NATO[ch] || ch).join(' ');
const LEVELS = [null, { name: 'One at a time', n: [1, 1] }, { name: 'A couple', n: [1, 2] }, { name: 'Small pileup', n: [2, 3] }, { name: 'Busy', n: [3, 5] }, { name: 'Big pileup', n: [5, 8] }];

/* ---------------- voices ---------------- */
let VO = [];
const ANDROID = /Android/i.test(navigator.userAgent);
let lastCancel = 0, lastErr = '';
function loadVoices() {
  const v = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  VO = v.filter(x => /^en[-_]/i.test(x.lang));
  if (ANDROID) { const loc = VO.filter(x => x.localService); if (loc.length) VO = loc; } // network voices often fail silently on Android
  if (!VO.length) VO = v;
}
if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }
function speak(text, who) {
  // some Android phones drop an utterance spoken right after cancel(): wait a moment first
  const gap = Math.max(0, 150 - (Date.now() - lastCancel));
  // while you're keyed up (transmitting) you can't hear anybody: let the time pass silently
  if (typeof recOn !== 'undefined' && recOn) return new Promise(r0 => setTimeout(() => r0(false), 400 + text.length * 45));
  return new Promise(r0 => setTimeout(r0, gap)).then(() => speakNow(text, who));
}
function speakNow(text, who) {
  return new Promise(res => {
    if (!window.speechSynthesis) { res(false); return; }
    if (speechSynthesis.paused) speechSynthesis.resume();
    const u = new SpeechSynthesisUtterance(text); window.__kpcU = u; // keep a reference (Chrome can lose a garbage-collected utterance's events)
    if (!VO.length) loadVoices();
    if (who && VO.length) {
      // pick a man's or woman's voice when the device has both; otherwise the pitch does the work
      const MALE = /\b(male|man|david|mark|guy|daniel|fred|alex|tom|aaron|arthur|george|james|rishi|eddy|reed|ralph|bruce|junior|lee|oliver|thomas)\b/i;
      const pool = VO.filter(v => who.m ? MALE.test(v.name) : !MALE.test(v.name));
      const list = pool.length ? pool : VO; u.voice = list[who.vi % list.length]; u.lang = u.voice.lang;
    } else u.lang = 'en-US';
    u.rate = who ? who.rate : 1; u.pitch = who ? who.pitch : 1; u.volume = Math.max(0.15, Math.min(1, (who ? who.vol : 1) * S.vol));
    let done = false, spoke = false; const fin = () => { if (!done) { done = true; clearTimeout(tm); res(spoke); } };
    const tm = setTimeout(fin, 1500 + text.length * 95 / u.rate); // some browsers never fire 'end'
    u.onstart = () => { spoke = true; }; u.onend = () => { spoke = true; fin(); }; u.onerror = e => { lastErr = (e && e.error) || 'error'; if (lastErr !== 'interrupted' && lastErr !== 'canceled' && Date.now() - lastCancel > 400) { const d = $('vbDiag'); if (d) d.textContent = 'Voice problem: ' + lastErr + '. Tap TEST VOICE to check.'; } fin(); };
    speechSynthesis.speak(u);
  });
}
function hush() { if (window.speechSynthesis) { speechSynthesis.cancel(); lastCancel = Date.now(); } }
/* phones only let a page talk after a tap: say something short right inside the tap */
function unlock() { try { if (!window.speechSynthesis) return; loadVoices(); const u = new SpeechSynthesisUtterance('Ready'); u.lang = 'en-US'; u.volume = 0.6; speechSynthesis.speak(u); } catch (e) {} }
function testVoice() {
  unlock(); loadVoices();
  const all = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  const d = $('vbDiag'); if (d) d.textContent = !window.speechSynthesis ? 'This browser has no speech voices.' : `Voices found: ${all.length} (${VO.length} English${ANDROID ? ' on-phone' : ''}). ${VO[0] ? 'First: ' + VO[0].name + '.' : ''} ${lastErr ? 'Last error: ' + lastErr + '.' : ''} If you hear nothing: turn the media volume up (not the ringer), and on Android check Settings → Text-to-speech has an English voice installed.`;
  setTimeout(() => speakNow('Kilo Four Tango Echo Sierra Tango, you are five nine, Kentucky.', VO.length ? { vi: 0, rate: 1, pitch: 1, vol: 1 } : null), 900);
}

/* ---------------- band hiss (Web Audio) ---------------- */
let AC = null, nG = null;
function hiss(on) {
  try {
    if (!AC) {
      AC = new (window.AudioContext || window.webkitAudioContext)();
      const len = AC.sampleRate * 2, b = AC.createBuffer(1, len, AC.sampleRate), d = b.getChannelData(0); for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
      const s = AC.createBufferSource(); s.buffer = b; s.loop = true;
      const f = AC.createBiquadFilter(); f.type = 'bandpass'; f.frequency.value = 1400; f.Q.value = 0.6;
      nG = AC.createGain(); nG.gain.value = 0; s.connect(f); f.connect(nG); nG.connect(AC.destination); s.start();
    }
    if (AC.state === 'suspended') AC.resume();
    nG.gain.setTargetAtTime(on ? S.hiss * 0.25 : 0, AC.currentTime, on ? 0.15 : 0.02);
  } catch (e) {}
}

/* ---------------- state ---------------- */
const S = Object.assign({ call: '', st: 'KY', ref: '', level: 1, vol: 0.9, hiss: 0.3, rate: 1, mic: true, autolog: false, prog: 'pota', mode: 'act', p2p: false, band: '20' }, store.get('kpcSSB', {}));
const save = () => store.set('kpcSSB', S);
/* program: off (plain contacts), POTA, KFF (WWFF), SOTA */
const PROG = {
  off: { cq: 'CQ CQ CQ', where: '', ty: 'contact', goal: 0, to: '', refName: '' },
  pota: { cq: 'CQ Parks on the Air, CQ POTA', where: 'portable in a park', ty: 'park', goal: 10, to: 'park to park', refName: 'park', ref: () => 'US-' + String(rnd(1, 11000)).padStart(4, '0') },
  kff: { cq: 'CQ W W F F, CQ K F F', where: 'portable at a flora and fauna reference', ty: 'reference', goal: 44, to: 'K F F to K F F', refName: 'KFF reference', ref: () => 'KFF-' + String(rnd(1, 7000)).padStart(4, '0') },
  sota: { cq: 'CQ SOTA, CQ Summits on the Air', where: 'portable on a summit', ty: 'summit', goal: 4, to: 'summit to summit', refName: 'summit', ref: () => pick(['W4K/EC', 'W4C/WM', 'W4T/SU', 'W4V/SH', 'W8V/SR']) + '-' + String(rnd(1, 140)).padStart(3, '0') }
};
const P = () => PROG[S.prog] || PROG.pota;
const sayRef = ref => String(ref).replace(/[A-Z]/g, c => c + ' ').replace(/\d/g, d => ' ' + ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'][+d] + ' ').replace(/[-/]/g, ' ').replace(/\s+/g, ' ').trim();
const run = { on: false, callers: [], cur: null, sent: false, last: '', log: [], t0: 0, gen: 0, worked: new Set() };
const myCall = () => (S.call || '').toUpperCase().trim() || 'K4TEST';

function status(t) { const e = $('vbStatus'); if (e) e.textContent = t; }
function line(who, text, cls) { const b = $('vbBand'); if (!b) return; const d = document.createElement('div'); d.className = 'vb-line ' + (cls || ''); d.innerHTML = `<b>${esc(who)}</b> ${esc(text)}`; b.appendChild(d); b.scrollTop = b.scrollHeight; while (b.children.length > 120) b.removeChild(b.firstChild); }
function showText() { return $('vbShow') && $('vbShow').checked; }

function arrivals() {
  const lv = LEVELS[S.level] || LEVELS[1], want = rnd(lv.n[0], lv.n[1]);
  while (run.callers.length < want) {
    const st = pickState(S.band, S.st); let c; do { c = newCall(st); } while (run.worked.has(c) || run.callers.some(x => x.call === c) || c === myCall());
    run.callers.push({ call: c, st, rst: pick(['59', '59', '59', '57', '58', '55', '44']), vi: rnd(0, 50), rate: (0.95 + Math.random() * 0.35) * S.rate, vol: 0.55 + Math.random() * 0.45 }); { const o = run.callers[run.callers.length - 1]; o.m = Math.random() < 0.65; o.pitch = o.m ? 0.5 + Math.random() * 0.3 : 1 + Math.random() * 0.3; if (P().ref && Math.random() < (S.prog === 'sota' ? 0.18 : 0.1)) o.ref = P().ref(); }
  }
}
async function callIn(list) {
  const g = run.gen; run.last = '';
  for (const o of list) {
    if (g !== run.gen) return;
    const twice = chance(S.level >= 3 ? 0.25 : 0.5);
    const t = (o.ref ? P().to + ', ' : '') + say1(o.call) + (twice ? ', ' + say1(o.call) : '');
    if (showText()) line(o.call, (o.ref ? P().to.toUpperCase() + ' ' : '') + o.call + (twice ? ' ' + o.call : ''), 'them');
    else line('📢', 'a station calls', 'them');
    await speak(t, o);
    if (S.level >= 3 && chance(0.4)) await new Promise(r => setTimeout(r, rnd(0, 150)));
  }
}
function start() {
  if (!/^[A-Z0-9]{1,3}\d[A-Z]{1,4}$/.test(myCall())) { status('Enter your call sign first.'); $('vbCall').focus(); return; }
  unlock(); run.gen++; Object.assign(run, { on: true, callers: [], cur: null, sent: false, t0: Date.now() });
  hiss(true); $('vbGo').textContent = '■ STOP'; $('vbGo').classList.add('stop');
  status(`Level ${S.level}: ${LEVELS[S.level].name}. Call CQ to start.`);
  form(true);
}
function stop() { hush(); run.gen++; run.on = false; hiss(false); $('vbGo').textContent = '▶ START'; $('vbGo').classList.remove('stop'); status('Stopped.'); form(false); }
function form(on) { ['vbCq', 'vbQrz', 'vbAgn', 'vbSend', 'vbLog', 'vbTalk', 'vbSkip', 'vb73', 'vbQsl', 'hCall', 'hRep', 'hAgn', 'hNeg', 'hLeave'].forEach(id => { const e = $(id); if (e) e.disabled = !on; }); }

async function cq() {
  if (!run.on) return;
  hush(); run.gen++;
  line('YOU', `${P().cq}, this is ${myCall()} ${say1(myCall())}, ${myCall()}${P().where ? ' ' + P().where : ''}${S.ref && S.prog !== 'off' ? ' ' + S.ref : ''}.`, 'you');
  arrivals(); await new Promise(r => setTimeout(r, 500)); await callIn(run.callers.slice());
}
async function qrz() {
  if (!run.on) return; hush(); run.gen++;
  const part = ($('fCall').value || '').toUpperCase().replace(/[^A-Z0-9/]/g, '');
  if (part && part.length < 4) {
    const hit = run.callers.filter(c => c.call.includes(part));
    line('YOU', `The station with ${say1(part)}, go ahead.`, 'you');
    if (hit.length) { await callIn(hit); } else line('', 'Nobody with that in their call.', 'note');
    return;
  }
  line('YOU', `QRZ? ${myCall()}`, 'you'); if (chance(0.5)) arrivals(); await callIn(run.callers.slice());
}
async function agn() {
  if (!run.on) return; hush(); run.gen++;
  line('YOU', 'Again, again?', 'you');
  if (run.cur && run.sent) { await theirExchange(run.cur, true); } else await callIn(run.callers.slice());
}
const base = c => c.replace(/\/.*$/, '');
function lev(a, b) { const m = a.length, n = b.length, d = []; for (let i = 0; i <= m; i++) { d[i] = [i]; } for (let j = 1; j <= n; j++) d[0][j] = j; for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); return d[m][n]; }
async function sendReport(opt) {
  if (!run.on) return;
  let c = ($('fCall').value || '').toUpperCase().trim();
  // spoken call: speech-to-text sometimes gets one letter wrong ("Bravo" heard as "Brava"), so match it to the station it's closest to
  if (opt && opt.speech && c && !run.callers.some(x => x.call === c)) {
    const best = run.callers.map(x => [x, lev(x.call, c)]).sort((a, b) => a[1] - b[1]);
    if (best[0] && best[0][1] <= 1 && !(best[1] && best[1][1] === best[0][1])) { line('', `🎙 Heard ${c}, matched to ${best[0][0].call}.`, 'note'); c = best[0][0].call; $('fCall').value = c; }
  }
  const rs = ($('fSent').value || '59').trim();
  if (!c) { status('Type the call you heard in the CALL box first.'); $('fCall').focus(); return; }
  hush(); run.gen++;
  line('YOU', `${c}, you're ${rs} ${STN[S.st] || S.st}${S.ref && S.prog !== 'off' ? ', ' + P().refName + ' ' + S.ref : ''}. ${myCall()}.`, 'you');
  let o = run.callers.find(x => x.call === c);
  if (!o) {
    const near = run.callers.find(x => lev(x.call, c) <= 2);
    if (near) { run.cur = near; run.sent = true; const d = lev(near.call, c); line('', `You sent ${c}: ${d === 1 ? 'one letter or number is' : 'a couple of letters are'} off. Listen to how they say it.`, 'note'); if (showText()) line(near.call, `Negative, ${near.call}`, 'them'); await speak(`Negative. ${say1(near.call)}. ${say1(near.call)}.`, near); status('They corrected you. Fix the CALL box (no penalty yet, but it counts if you log it wrong).'); return; }
    line('', 'Nobody answers. Nobody with that call is calling you: try AGN or QRZ.', 'note'); return;
  }
  run.cur = o; run.sent = true; o.t0 = Date.now();
  await theirExchange(o, false);
}
async function theirExchange(o, again) {
  const g = run.gen;
  const st = STN[o.st] || o.st;
  const refTxt = o.ref ? ` I'm at ${P().refName} ${sayRef(o.ref)}, ${sayRef(o.ref)}.` : '', thx = P().ty === 'contact' ? 'Thanks for the contact.' : `Thanks for the ${P().ty}.`;
  const t = again ? `You're ${say1(o.rst)}, ${st}. ${st}.${refTxt}` : pick([`Thanks! You're ${say1(o.rst)} ${say1(o.rst)}, ${st}, ${st}.${refTxt}`, `Roger, thank you. ${say1(o.rst)} into ${st}.${refTxt} ${thx}`, `Good copy. You're ${say1(o.rst)}, ${st}.${refTxt}`]);
  if (showText()) line(o.call, t.replace(/[A-Za-z-]+ (?=[A-Za-z-]+ )/g, m => m), 'them'); else line(o.call.slice(0, 0) + '📢', 'they give you their report and state', 'them');
  if (g !== run.gen) return;
  await speak(t, o);
  if (S.autolog && g === run.gen) { $('fRcvd').value = o.rst; $('fSt').value = o.st; if (o.ref && $('fRef')) $('fRef').value = o.ref; status('Auto log filled in their report and state. Say or tap THANKS, 73 and it logs itself.'); return; }
  status('Log their report and state, then press LOG IT (you say "thanks, 73, QRZ").');
}
function check(o, f) {
  const errs = [];
  if (f.call !== o.call) errs.push(`call: you logged ${f.call || '(blank)'}, it was ${o.call}`);
  if (f.rcvd.replace(/\D/g, '') !== o.rst) errs.push(`their report: you logged ${f.rcvd || '(blank)'}, they gave ${o.rst}`);
  const stOk = f.st === o.st || (STN[o.st] || '').toUpperCase() === f.st;
  if (!stOk) errs.push(`state: you logged ${f.st || '(blank)'}, it was ${o.st} (${STN[o.st]})`);
  if (o.ref && (f.ref || '').replace(/\s/g, '') !== o.ref) errs.push(`their ${P().refName}: you logged ${f.ref || '(blank)'}, it was ${o.ref}`);
  return errs;
}
const sayBye = o => { const bye = pick(['Thanks, seventy-three!', `Seventy-three, thanks for the ${P().ty}!`, 'Thank you, seventy-three.', 'Thanks for the contact, seventy-three.']); if (showText()) line(o.call, bye.replace(/seventy-three/gi, '73'), 'them'); return speak(bye, o); };
/* you said "thanks, 73" on the mic: they sign too, but YOU still do the logging (that's the skill we're practicing) */
async function say73(words) {
  if (!run.on) return;
  const o = run.cur && run.sent ? run.cur : null;
  hush(); run.gen++; line('YOU', typeof words === 'string' ? words : 'Thanks, 73.', 'you');
  if (!o) { status('Thanks, 73! Nobody to sign with right now. Call CQ or QRZ.'); return; }
  o.signed = true; const g = run.gen; await sayBye(o); if (g !== run.gen) return;
  if (S.autolog) { if (!$('fRcvd').value) $('fRcvd').value = o.rst; if (!$('fSt').value) $('fSt').value = o.st; if (o.ref && $('fRef') && !$('fRef').value) $('fRef').value = o.ref; return logIt(true); }
  status('Now log it: check CALL, fill RCVD and STATE, then press ✓ LOG IT.'); const r0 = $('fRcvd'); if (r0 && !r0.value) r0.focus({ preventScroll: true });
}
/* can't get a call? skip that station (nothing goes in the log) */
async function skip() {
  if (!run.on) return;
  const typed = ($('fCall').value || '').toUpperCase().trim();
  const o = (run.cur && run.sent) ? run.cur : run.callers.find(x => x.call === typed) || run.callers[0];
  hush(); run.gen++;
  if (!o) { status('Nobody to skip. Call CQ.'); return; }
  run.callers = run.callers.filter(x => x !== o); run.cur = null; run.sent = false; run.skipped = (run.skipped || 0) + 1;
  line('', `⏭ Skipped a station (it was ${o.call}). No penalty: it just doesn't go in the log.`, 'note');
  ['fCall', 'fRcvd', 'fSt', 'fRef'].forEach(id => { if ($(id)) $(id).value = ''; }); $('fSent').value = '59';
  if (chance(0.6)) arrivals();
  if (run.callers.length) { await new Promise(r0 => setTimeout(r0, 300)); await callIn(run.callers.slice()); } else status('Nobody calling. Call CQ again.');
}
async function logIt(auto) {
  if (S.mode === 'hunt') return H.on ? huntLog() : undefined;
  if (!run.on) return;
  const f = { call: ($('fCall').value || '').toUpperCase().trim(), sent: ($('fSent').value || '59').trim(), rcvd: ($('fRcvd').value || '').trim(), st: ($('fSt').value || '').toUpperCase().trim(), ref: (($('fRef') || {}).value || '').toUpperCase().trim() };
  const o = run.cur && run.sent ? run.cur : run.callers.find(x => x.call === f.call);
  if (!f.call) { status('Nothing to log yet.'); return; }
  const errs = o ? check(o, f) : [`${f.call} never called you`];
  const q = { auto: !!(auto === true || S.autolog), ref: f.ref, n: run.log.length + 1, time: new Date(), call: f.call, sent: f.sent, rcvd: f.rcvd, st: f.st, ok: !errs.length, errs, secs: o && o.t0 ? Math.round((Date.now() - o.t0) / 1000) : 0, truth: o ? `${o.call} ${o.rst} ${o.st}` : '' };
  run.log.push(q); drawLog();
  hush(); run.gen++;
  const signed = o && o.signed;
  if (!signed) line('YOU', `Thanks, 73. QRZ? ${myCall()}`, 'you');
  if (errs.length) line('', '⚠ Log check: ' + errs.join(' · '), 'bad'); else line('', '✓ Logged correctly.', 'good');
  if (o) {
    run.callers = run.callers.filter(x => x !== o); run.worked.add(o.call);
    // they sign too: "thanks, 73"
    if (!signed) { const g = run.gen; await sayBye(o); if (g !== run.gen) return; }
  }
  run.cur = null; run.sent = false;
  ['fCall', 'fRcvd', 'fSt', 'fRef'].forEach(id => { if ($(id)) $(id).value = ''; }); $('fSent').value = '59'; $('fCall').focus();
  if (chance(0.6)) arrivals();
  if (run.callers.length) { await new Promise(r => setTimeout(r, 400)); await callIn(run.callers.slice()); }
  else status('Nobody calling. Call CQ again.');
  const good = run.log.filter(x => x.ok).length;
  if (good && good % 10 === 0 && S.level < 5 && run.log.slice(-10).every(x => x.ok)) { status(`10 clean contacts in a row! Try level ${S.level + 1}.`); }
}
function drawLog() {
  if (S.mode === 'hunt') return drawHuntLog();
  const tb = $('vbLogB'); if (!tb) return;
  tb.innerHTML = run.log.slice().reverse().map(q => `<tr class="${q.ok ? 'ok' : 'bad'}"><td>${q.n}</td><td>${q.time.toISOString().slice(11, 16)}</td><td><b>${esc(q.call)}</b></td><td>${esc(q.sent)}</td><td>${esc(q.rcvd)}</td><td>${esc(q.st)}${q.ref ? '<br><small>' + esc(q.ref) + '</small>' : ''}</td><td>${q.auto ? '🤖 ' : ''}${q.ok ? '✓' : '<span title="' + esc(q.errs.join('; ')) + '">✗ ' + esc(q.truth) + '</span>'}</td><td><button type="button" class="vb-qsl" data-qsl="${q.n}" title="Print a QSL card" aria-label="Print a QSL card for ${esc(q.call)}">🖨</button></td></tr>`).join('');
  const man = run.log.filter(q => !q.auto), n = run.log.length, ok = man.filter(q => q.ok).length, mins = Math.max(1, (Date.now() - run.t0) / 60000);
  const e = $('vbStats'); if (e) e.innerHTML = `<div><b>${n}</b><span>contacts</span></div><div><b>${man.length ? Math.round(ok / man.length * 100) + '%' : '—'}</b><span>logged right (by you)</span></div><div><b>${Math.round(n / mins * 60)}</b><span>per hour</span></div>` + (P().goal ? `<div><b>${Math.min(n, P().goal)}/${P().goal}</b><span>${n >= P().goal ? '🎉 activated!' : 'to activate'}</span></div>` : '');
}
/* print a practice QSL card for one contact (marked PRACTICE so it can't pass as a real card) */
function qslPrint(n) {
  const hunt = S.mode === 'hunt', q = (hunt ? H.log : run.log).find(x => x.n === n); if (!q) return;
  const me = myCall(), d = q.time, date = d.toISOString().slice(0, 10), utc = d.toISOString().slice(11, 16);
  const band = (hunt ? q.band : S.band || '20') + 'm', st = STN[S.st] || S.st;
  const progName = { pota: 'Parks on the Air', kff: 'World Wide Flora & Fauna (KFF)', sota: 'Summits on the Air' };
  const where = hunt ? (q.ref ? `You were at ${q.ref}` : '') : (S.ref && S.prog !== 'off' ? `Activating ${S.ref} · ${progName[S.prog] || ''}` : '');
  const f = document.createElement('iframe'); f.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0'; document.body.appendChild(f);
  f.contentDocument.open(); f.contentDocument.write(`<!doctype html><html><head><meta charset="utf-8"><title>QSL ${esc(q.call)}</title><style>@page{size:letter;margin:.5in}body{margin:0;font-family:Arial,sans-serif;color:#111}
  .card{width:5.5in;height:3.5in;border:2px dashed #999;padding:.18in;box-sizing:border-box;position:relative;background:linear-gradient(135deg,#fff8e6,#eef7ee);margin:0 auto}
  .top{display:flex;gap:12px;align-items:center}.top img{width:62px;height:62px}.call{font:900 46px Georgia,serif;letter-spacing:1px;color:#073b4c;line-height:1}.sub{font:700 12px Arial;color:#1d5a3a;letter-spacing:1px}
  table{width:100%;border-collapse:collapse;margin-top:12px;font-size:13px}th{background:#073b4c;color:#fff;font-size:10px;letter-spacing:1px;padding:4px}td{border:1px solid #073b4c;text-align:center;padding:6px 4px;font:700 15px "Courier New",monospace}
  .to{font:700 15px Arial;margin-top:10px}.to b{font:900 20px "Courier New",monospace}.w{font-size:12px;margin-top:6px;color:#333}
  .pr{position:absolute;right:.18in;top:.18in;border:3px solid #c1121f;color:#c1121f;font:900 13px Arial;padding:3px 8px;transform:rotate(6deg);letter-spacing:2px}
  .ft{position:absolute;left:.18in;right:.18in;bottom:.14in;display:flex;justify-content:space-between;font-size:11px;color:#333}.tip{text-align:center;font-size:11px;color:#666;margin-top:10px}</style></head><body>
  <div class="card"><div class="pr">PRACTICE</div><div class="top"><img src="KPC-logo.png" alt=""><div><div class="call">${esc(me)}</div><div class="sub">KENTUCKY PORTABLE CLUB · ${esc(st.toUpperCase())}</div></div></div>
  <div class="to">To radio: <b>${esc(q.call)}</b></div>
  <table><tr><th>DATE</th><th>UTC</th><th>BAND</th><th>MODE</th><th>${hunt ? 'RST RCVD' : 'RST SENT'}</th></tr><tr><td>${date}</td><td>${utc}</td><td>${band}</td><td>SSB</td><td>${esc(hunt ? q.rcvd : q.sent)}</td></tr></table>
  <div class="w">${esc(where)}</div>
  <div class="w" style="margin-top:14px;font-weight:700">☐ PSE QSL &nbsp; ☑ TNX QSL &nbsp;&nbsp; Op: ____________________</div>
  <div class="ft"><span>Tnx for the QSO, 73!</span><span>Made in KPC Voice Pileup Practice: not a real contact</span></div></div>
  <div class="tip">Cut on the dashed line. Real hams trade cards like this to confirm a contact!</div></body></html>`);
  f.contentDocument.close();
  const im = f.contentDocument.images[0]; const go = () => { try { f.contentWindow.focus(); f.contentWindow.print(); } catch (e) {} setTimeout(() => f.remove(), 60000); };
  if (!im || im.complete) setTimeout(go, 200); else im.onload = im.onerror = go;
}
function adif() {
  const hunt = S.mode === 'hunt';
  if (!(hunt ? H.log : run.log).length) return;
  const f = (k, v) => v ? `<${k}:${String(v).length}>${v} ` : '';
  const rows = hunt ? huntAdif() : run.log.map(q => { const d = q.time.toISOString(); return f('CALL', q.call) + f('QSO_DATE', d.slice(0, 10).replace(/-/g, '')) + f('TIME_ON', d.slice(11, 16).replace(':', '')) + f('BAND', (S.band || '20') + 'M') + f('MODE', 'SSB') + f('RST_SENT', q.sent) + f('RST_RCVD', q.rcvd) + f('STATE', q.st) + f('STATION_CALLSIGN', myCall()) + (S.prog === 'sota' ? f('MY_SOTA_REF', S.ref) + f('SOTA_REF', q.ref) : f('MY_SIG', S.ref && S.prog !== 'off' ? (S.prog === 'kff' ? 'WWFF' : 'POTA') : '') + f('MY_SIG_INFO', S.prog !== 'off' ? S.ref : '') + f('SIG', q.ref ? (S.prog === 'kff' ? 'WWFF' : 'POTA') : '') + f('SIG_INFO', q.ref)) + f('COMMENT', 'KPC PRACTICE - NOT A REAL QSO') + '<EOR>'; });
  const txt = 'KPC Voice Pileup Practice log (PRACTICE ONLY - do not upload to POTA)\n<ADIF_VER:5>3.1.4 <PROGRAMID:3>KPC <EOH>\n' + rows.join('\n') + '\n';
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'text/plain' })); a.download = `KPC-practice-${myCall() || 'log'}.adi`; a.click();
}

/* ================= HUNT MODE =================
   A pretend spots page (like pota.app / SOTAwatch). Tune to a spot, listen to the activator work the pileup,
   throw your call at the right moment, give your report, then log them. Some spots are busted (the call on the
   spot is wrong), some activators copy your call wrong (say NEGATIVE and correct them), and working the same
   park twice is a dupe. */
let KYD = null;
fetch('kpc-ky-data.json').then(r => r.json()).then(d => { KYD = d; }).catch(() => {});
const H = { on: false, spots: [], cur: null, gen: 0, phase: 'idle', log: [], qsos: [], pending: null, called: 0, calledAt: 0, tries: 0, doubled: 0, spotsGiven: 0, wait: null, timer: null };
const huntProg = () => (S.prog === 'kff' || S.prog === 'sota') ? S.prog : 'pota';
const PROGNAME = { pota: 'POTA', kff: 'KFF', sota: 'SOTA' };
function huntRef(prog, band) {
  const where = pickState(band, S.st), ky = where === 'KY';
  if (prog === 'sota') {
    if (ky && KYD && KYD.summits && KYD.summits.length) { const s = pick(KYD.summits); return { ref: s.c, name: s.n, st: 'KY' }; }
    const AS = { NC: 'W4C/WM', TN: 'W4T/SU', VA: 'W4V/SH', WV: 'W8V/SR', GA: 'W4G/NG', CO: 'W0C/FR', CA: 'W6/CT', AZ: 'W7A/MN', OR: 'W7O/CM', WA: 'W7W/KG', NY: 'W2/GA', NH: 'W1/HA', VT: 'W1/NL', ME: 'W1/AM', TX: 'W5T/HE', NM: 'W5N/SI', UT: 'W7U/SL', MT: 'W7M/BR', ID: 'W7I/SR', PA: 'W3/PD', AR: 'W5A/OZ', MO: 'W0M/OZ', NV: 'W7N/CC', WY: 'W7Y/MA', SC: 'W4C/US', AL: 'W4A/NE', OK: 'W5O/NE', MA: 'W1/MB', SD: 'W0D/BH', MN: 'W0M/NE', MI: 'W8M/UP', WI: 'W9/WI', OH: 'W8O/SO', IN: 'W9/IN', IL: 'W9/IL', MD: 'W3/WE', NJ: 'W2/NJ', CT: 'W1/CT', IA: 'W0I/IA', NE: 'W0N/NE', KS: 'W0K/KS', ND: 'W0D/ND', LA: 'W5L/LA', MS: 'W5M/MS', FL: 'W4F/FL', DE: 'W3/DE', RI: 'W1/RI' };
    const a = [AS[where] || 'W4T/SU', AS[where] ? where : 'TN'];
    return { ref: a[0] + '-' + String(rnd(1, 140)).padStart(3, '0'), name: 'a summit in ' + STN[a[1]], st: a[1] };
  }
  if (prog === 'kff') {
    if (ky && KYD && KYD.kff && KYD.kff.length) { const s = pick(KYD.kff); return { ref: s.c, name: s.n, st: 'KY' }; }
    const st = where; return { ref: 'KFF-' + String(rnd(1, 7000)).padStart(4, '0'), name: 'a reference in ' + STN[st], st };
  }
  if (ky && KYD && KYD.parks && KYD.parks.length) { const s = pick(KYD.parks.filter(p => p.n && p.n.length < 50)); return { ref: s.c, name: s.n, st: 'KY' }; }
  const st = where; return { ref: 'US-' + String(rnd(1, 11000)).padStart(4, '0'), name: 'a park in ' + STN[st], st };
}
function voiceFor() { const m = Math.random() < 0.65; return { vi: rnd(0, 50), rate: (0.95 + Math.random() * 0.3) * S.rate, vol: 0.6 + Math.random() * 0.4, m, pitch: m ? 0.5 + Math.random() * 0.3 : 1 + Math.random() * 0.3 }; }
function bust(c) { const i = rnd(c.search(/\d/) + 1, c.length - 1), ch = c[i]; let n; do { n = L(); } while (n === ch); return c.slice(0, i) + n + c.slice(i + 1); }
const COMMENTS = ['QRV SSB', 'tnx QSO', 'good signal', 'QSB', 'big pileup!', 'weak here', '5/9 into KY', 'first time activator', 'tnx for the park', 'loud'];
function newSpot() {
  const prog = huntProg(), band = pick(['20', '20', '20', '40', '40', '17']), r = huntRef(prog, band);
  let call; do { call = newCall(r.st); } while (H.spots.some(s => s.call === call) || call === myCall());
  const fr = band === '20' ? 14200 + rnd(5, 140) + pick([0, 0, 0.5]) : band === '40' ? 7180 + rnd(0, 110) + pick([0, 0.5]) : 18130 + rnd(0, 30);
  const busted = Math.random() < 0.15;
  const lvMax = (LEVELS[S.level] || LEVELS[1]).n[1];
  return Object.assign({ id: Math.random().toString(36).slice(2, 8), prog, call, shown: busted ? bust(call) : call, busted, band, fr: fr.toFixed(1), born: Date.now() - rnd(0, 8) * 60000, life: rnd(5, 14) * 60000, pile: rnd(0, lvMax), comment: pick(COMMENTS), spotter: newCall(pickState(band, S.st)), qrt: false, rst: pick(['59', '59', '57', '58', '55']), cnt: rnd(1, 9) }, r, { v: voiceFor() });
}
function huntStart() {
  if (!/^[A-Z0-9]{1,3}\d[A-Z]{1,4}$/.test(myCall())) { status('Enter your call sign first.'); $('vbCall').focus(); return; }
  unlock(); H.on = true; run.on = true; H.gen++; H.cur = null; H.phase = 'idle'; run.t0 = Date.now();
  if (!H.spots.length || H.spots[0].prog !== huntProg()) H.spots = Array.from({ length: 7 }, newSpot);
  $('vbGo').textContent = '■ STOP'; $('vbGo').classList.add('stop'); form(true); hiss(true);
  status('Pick a spot and press TUNE to listen in.'); drawSpots(); drawTuned();
  clearInterval(H.timer); H.timer = setInterval(spotTick, 5000);
}
function huntStop() { H.on = false; run.on = false; H.gen++; hush(); hiss(false); clearInterval(H.timer); H.cur = null; H.phase = 'idle'; $('vbGo').textContent = '▶ START'; $('vbGo').classList.remove('stop'); form(false); status('Stopped.'); drawSpots(); drawTuned(); }
function spotTick() {
  if (!H.on) return;
  const now = Date.now();
  H.spots.forEach(s => { if (!s.qrt && s !== H.cur && now - s.born > s.life) s.qrt = true; });
  H.spots = H.spots.filter(s => !(s.qrt && now - s.born > s.life + 120000 && s !== H.cur));
  if (H.spots.filter(s => !s.qrt).length < 6 || Math.random() < 0.12) { const s = newSpot(); s.born = now; H.spots.unshift(s); }
  drawSpots();
}
const ago = t => { const m = Math.round((Date.now() - t) / 60000); return m < 1 ? 'just now' : m + ' min ago'; };
function workedRight(s) { return H.log.some(q => q.ok && q.trueCall === s.call && q.trueRef === s.ref); }
function drawSpots() {
  const box = $('vbSpots'); if (!box) return;
  if (!H.on) { box.innerHTML = '<p class="vb-sp-empty">Press ▶ START to load the practice spots.</p>'; return; }
  const list = H.spots.slice().sort((a, b) => (a.qrt - b.qrt) || (b.born - a.born));
  box.innerHTML = list.map(s => `<div class="vb-sp${s === H.cur ? ' on' : ''}${s.qrt ? ' qrt' : ''}">
    <div class="vb-sp-a"><b>${esc(s.shown)}</b><span>${esc(s.fr)} kHz · SSB</span></div>
    <div class="vb-sp-p"><b>${esc(s.ref)}</b> ${esc(s.name)} <i>(${esc(s.st)})</i></div>
    <div class="vb-sp-m">${s.qrt ? '<span class="tag">QRT</span> ' : ''}${workedRight(s) ? '<span class="tag ok">✓ WORKED</span> ' : ''}"${esc(s.comment)}" · by ${esc(s.spotter)} · ${ago(s.born)} · ${s.cnt} spots</div>
    <div class="vb-sp-b">${s.qrt ? '' : `<button type="button" class="vb-btn${s === H.cur ? '' : ' alt'}" data-tune="${s.id}">${s === H.cur ? '📻 LISTENING' : '📻 TUNE'}</button>`}${workedRight(s) && !s.respotted && !s.qrt ? `<button type="button" class="vb-btn alt" data-respot="${s.id}">📢 RE-SPOT</button>` : ''}</div>
  </div>`).join('');
}
function drawTuned() {
  const t = $('vbTuned'); if (!t) return;
  const s = H.cur;
  t.innerHTML = s ? `📻 Tuned to <b>${esc(s.fr)} kHz</b> · spot says <b>${esc(s.shown)}</b> at ${esc(s.ref)} · <span id="vbPhase">${phaseText()}</span>` : 'Not tuned to anyone. Pick a spot above.';
}
function phaseText() { return { idle: '', cq: 'they\'re calling CQ', window: '🟢 your turn: call now!', qso: '🔴 they\'re working someone, wait', partial: '🟡 they want the rest of a call', mine: '🟢 they\'re talking to YOU', done: 'contact done, log it', qrt: 'they went QRT' }[H.phase] || ''; }
function setPhase(p) { H.phase = p; const e = $('vbPhase'); if (e) e.textContent = phaseText(); }
function tune(id) {
  const s = H.spots.find(x => x.id === id); if (!s || s.qrt) return;
  hush(); H.gen++; H.cur = s; H.called = 0; H.tries = 0; H.wait = null;
  s.life = Math.max(s.life, Date.now() - s.born + rnd(4, 8) * 60000); // stay on long enough to get a turn
  $('vbBand').innerHTML = ''; line('', `📻 Tuning to ${s.fr} kHz. Listen first: copy the activator's call and park from the air, not just the spot.`, 'note');
  ['fCall', 'fRcvd', 'fRef'].forEach(k => { if ($(k)) $(k).value = ''; }); $('fSent').value = '59';
  drawSpots(); drawTuned(); actLoop(s, H.gen);
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function waitFor(fn, ms, g) { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (g !== H.gen) return 'gone'; const v = fn(); if (v) return v; await sleep(150); } return null; }
async function aSay(s, spoken, shown) {
  const g = H.gen;
  await waitFor(() => !recOn, 10000, g); // they wait while you're transmitting
  if (g !== H.gen) return;
  const txt = shown || spoken;
  if (showText()) line(s.call, txt, 'them'); else line('📢', 'the activator talks', 'them');
  for (let i = 0; i < 2; i++) {
    H.cut = false;
    const ok = await speak(spoken, s.v);
    if (g !== H.gen) return;
    if (H.cut) { await waitFor(() => !recOn && Date.now() - recOffAt > 300, 10000, g); if (g !== H.gen) return; line('', '🔁 You keyed up over them, so they say it again:', 'note'); if (!showText()) line(s.call, txt, 'them'); continue; }
    if (!ok && !showText()) line(s.call, txt + '  (in words, in case the voice didn\'t play)', 'them');
    return;
  }
}
async function actLoop(s, g) {
  const pg = PROGNAME[s.prog], refS = sayRef(s.ref);
  const hunters = () => { const n = Math.max(0, s.pile + rnd(-1, 1)); return Array.from({ length: n }, () => { const st = pickState(s.band, S.st); return Object.assign({ call: newCall(st), st, rst: pick(['59', '59', '57', '58']) }, voiceFor()); }); };
  let first = true;
  await sleep(600);
  while (g === H.gen) {
    if (Date.now() - s.born > s.life + 60000) { await aSay(s, `Thanks everyone, I'm going Q R T. Seventy-three from ${say1(s.call)}.`, `Thanks everyone, I'm going QRT. 73 from ${s.call}.`); s.qrt = true; setPhase('qrt'); drawSpots(); status('They went QRT (off the air). Pick another spot.'); return; }
    setPhase('cq');
    const cqWords = s.prog === 'sota' ? 'CQ SOTA, CQ SOTA' : s.prog === 'kff' ? 'CQ K F F, CQ W W F F' : 'CQ POTA, CQ Parks on the Air';
    if (first || chance(0.3)) await aSay(s, `${cqWords}, this is ${say1(s.call)}, ${say1(s.call)}, at ${s.prog === 'sota' ? 'summit' : s.prog === 'kff' ? 'reference' : 'park'} ${refS}, ${s.name}.`, `${cqWords.replace('K F F', 'KFF').replace('W W F F', 'WWFF')}, this is ${s.call}, ${s.call}, at ${s.ref}, ${s.name}.`);
    else await aSay(s, `Q R Zee? ${say1(s.call)}, ${pg}.`, `QRZ? ${s.call}, ${pg}.`);
    first = false; if (g !== H.gen) return;
    /* the window: everybody calls */
    setPhase('window'); const w0 = Date.now() - 1200; H.called = 0;
    const hs = hunters();
    for (const h of hs) { if (g !== H.gen) return; if (recOn) { await sleep(500); continue; } if (showText()) line(h.call, h.call, 'them'); else line('📢', 'a hunter calls', 'them'); await speak(say1(h.call), h); }
    await waitFor(() => H.called && Date.now() - H.calledAt > 900, hs.length ? 1600 : 4500, g);
    if (!H.called && (recOn || Date.now() - recOffAt < 1500)) await waitFor(() => H.called || (!recOn && Date.now() - recOffAt > 2500), 9000, g); // you're still talking / the phone is still working out what you said
    if (g !== H.gen) return;
    const me = H.calledAt > w0 && H.called;
    if (!me && !hs.length) { await sleep(800); continue; }
    let pickMe = false;
    if (me) {
      const wMe = (1 + H.tries * 0.6) * (H.called >= 3 ? 0.5 : 1) * (S.p2p && S.ref ? 6 : 1);
      pickMe = Math.random() < wMe / (wMe + hs.length);
      if (!pickMe) H.tries++;
    }
    if (pickMe) {
      /* dupe? */
      if (H.qsos.some(q => q.s.call === s.call && q.s.ref === s.ref && q.heardRight)) { setPhase('mine'); await aSay(s, `${say1(myCall())}, we already worked, you're in the log. Thanks! Q R Zee?`, `${myCall()}, we already worked, you're in the log. Thanks! QRZ.`); line('', '🔁 Dupe! You already have this park in your log. Check your log before calling, and give someone else a turn.', 'note'); continue; }
      /* partial copy first sometimes */
      if (S.level >= 2 && chance(0.3)) {
        const part = myCall().slice(-2); setPhase('partial'); H.called = 0;
        await aSay(s, `The station with ${say1(part)}, again?`, `The station with ${part}, again?`);
        const ans = await waitFor(() => H.called ? 1 : null, 7000, g); if (g !== H.gen) return;
        if (!ans) { await aSay(s, `Lost them. Q R Zee?`, `Lost them. QRZ?`); continue; }
      }
      let heard = myCall(); const wrong = S.level >= 2 && chance(0.15); if (wrong) heard = bust(heard);
      setPhase('mine'); const st = STN[s.st] || s.st;
      const pend = { s, heard, rcvd: s.rst, sentRep: false, corrected: false, t0: Date.now() }; H.pending = pend;
      H.wait = null;
      const repLine = () => aSay(s, `${say1(heard)}, thanks for the call. You're ${say1(s.rst)}, ${say1(s.rst)}, ${st}.`, `${heard}, thanks for the call. You're ${s.rst}, ${s.rst}, ${st}.`);
      await repLine(); if (g !== H.gen) return;
      status(heard === myCall() ? 'They have you! Send your report: SEND MY REPORT (or say "QSL, you\'re five nine Kentucky, thanks, 73").' : 'Listen close: did they get your call right? If not, press NEGATIVE.');
      let asked = false;
      for (;;) {
        const ev = await waitFor(() => H.wait, asked ? 7000 : 11000, g); if (g !== H.gen) return; H.wait = null;
        if (!ev) { if (!asked) { asked = true; await aSay(s, `${say1(heard)}, are you there?`, `${heard}, are you there?`); continue; } await aSay(s, `Lost that one. Q R Zee?`, `Lost that one. QRZ?`); line('', 'They gave up waiting. Answer quicker next time: they have a pileup to work.', 'note'); H.pending = null; break; }
        if (ev === 'again') { await repLine(); continue; }
        if (ev === 'neg') { if (heard !== myCall()) { heard = myCall(); pend.heard = heard; pend.corrected = true; await aSay(s, `Sorry about that. ${say1(heard)}, roger. You're ${say1(s.rst)}, ${st}.`, `Sorry about that. ${heard}, roger. You're ${s.rst}, ${st}.`); } else { await aSay(s, `Roger, I have you as ${say1(heard)}. That's right.`, `Roger, I have you as ${heard}. That's right.`); } continue; }
        if (ev === 'report') {
          pend.sentRep = true; pend.done = Date.now(); pend.heardRight = heard === myCall(); H.qsos.push(pend);
          await aSay(s, pick([`QSL, thank you. Seventy-three.`, `Roger, thanks for the call. Seventy-three!`, `Thank you, seventy-three.`]));
          setPhase('done'); s.cnt++;
          if (!pend.heardRight) line('', `⚠ They logged you as ${heard} and you didn't correct them. That contact won't count for you. Press NEGATIVE next time.`, 'bad');
          status('Contact done! Log it: their CALL, RCVD (the report they gave you) and THEIR PARK, then ✓ LOG IT.');
          if (S.autolog) { $('fCall').value = s.call; $('fRcvd').value = s.rst; if ($('fRef')) $('fRef').value = s.ref; huntLog(true); }
          await sleep(1500); break;
        }
        if (ev === 'call') continue;
      }
      continue;
    }
    /* they work somebody else */
    const h = hs.length ? pick(hs) : null; if (!h) continue;
    setPhase('qso'); H.called = 0;
    await aSay(s, `${say1(h.call)}, you're five nine ${STN[s.st] || s.st}.`, `${h.call}, you're 59 ${STN[s.st] || s.st}.`); if (g !== H.gen) return;
    if (showText()) line(h.call, `QSL, ${h.rst} ${STN[h.st]}, thanks, 73.`, 'them'); else line('📢', 'the hunter answers', 'them');
    await speak(`QSL, ${say1(h.rst)}, ${STN[h.st]}. Thanks, seventy-three.`, h); if (g !== H.gen) return;
    await aSay(s, `Thank you, seventy-three.`);
    if (me && !pickMe) status(`They picked ${h.call} that time. Wait for QRZ, then call again. Calling once, clearly, works best.`);
  }
}
/* your buttons / your voice in hunt mode */
function hCall() {
  if (!H.on) return;
  if (!H.cur) { status('Tune to a spot first.'); return; }
  const p2p = S.p2p && S.ref;
  line('YOU', (p2p ? 'Park to park, ' : '') + myCall(), 'you');
  if (H.phase === 'qso') { H.doubled++; line('', '⚠ You called while they were working someone. That covers them up. Wait for "thanks, 73" or "QRZ".', 'bad'); return; }
  if (H.phase === 'mine') { H.wait = 'call'; return; }
  if (H.phase === 'cq') line('', 'Wait until they finish talking, then call.', 'note');
  H.called++; H.calledAt = Date.now();
  if (H.called === 3) line('', 'Tip: calling over and over can cover the activator. Call once, then listen.', 'note');
}
function hReport() {
  if (!H.on || !H.cur) return;
  const rs = ($('fSent').value || '59').trim(), st = STN[S.st] || S.st;
  const p2p = S.p2p && S.ref ? ` I'm at ${S.ref}.` : '';
  line('YOU', `QSL, you're ${rs} ${st}.${p2p} Thanks, 73.`, 'you');
  if (H.phase !== 'mine') { line('', 'They weren\'t talking to you yet. Wait until they say your call.', 'note'); return; }
  H.wait = 'report';
}
function hAgain() { if (!H.on || !H.cur) return; line('YOU', 'Again, again?', 'you'); if (H.phase === 'mine') H.wait = 'again'; else line('', 'Just listen: they\'ll say it again in a moment.', 'note'); }
function hNeg() { if (!H.on || !H.cur) return; line('YOU', `Negative. ${myCall()}, ${myCall()}.`, 'you'); if (H.phase === 'mine') H.wait = 'neg'; }
function hLeave() { hush(); H.gen++; H.cur = null; setPhase('idle'); drawSpots(); drawTuned(); status('Pick another spot.'); }
function respot(id) {
  const s = H.spots.find(x => x.id === id); if (!s) return;
  const c = prompt('Re-spot them. Add a short comment (like "tnx QSO, 59 in KY"):', 'tnx QSO'); if (c == null) return;
  s.respotted = true; s.born = Date.now(); s.spotter = myCall(); s.comment = c.slice(0, 40) || 'tnx QSO'; s.cnt++; H.spotsGiven++;
  line('', `📢 Thanks for re-spotting ${s.call}! Spots help activators get their contacts.`, 'good'); drawSpots(); drawLog();
}
function huntLog(auto) {
  const f = { call: ($('fCall').value || '').toUpperCase().trim(), sent: ($('fSent').value || '59').trim(), rcvd: ($('fRcvd').value || '').trim(), ref: (($('fRef') || {}).value || '').toUpperCase().replace(/\s/g, '') };
  if (!f.call) { status('Type their call in CALL first.'); return; }
  const p = H.qsos.slice().reverse().find(x => !x.logged && (x.s.call === f.call || x.s.shown === f.call)) || H.qsos.slice().reverse().find(x => !x.logged);
  const errs = [];
  if (!p) errs.push(`you never finished a contact with ${f.call}`);
  else {
    const s = p.s;
    if (f.call !== s.call) errs.push(f.call === s.shown && s.busted ? `call: the SPOT was wrong (${s.shown}). On the air they said ${s.call}. Always copy the call off the air` : `call: you logged ${f.call}, it was ${s.call}`);
    if (f.rcvd.replace(/\D/g, '') !== p.rcvd) errs.push(`their report: you logged ${f.rcvd || '(blank)'}, they gave you ${p.rcvd}`);
    if (f.ref !== s.ref) errs.push(`park: you logged ${f.ref || '(blank)'}, it was ${s.ref}`);
    if (!p.heardRight) errs.push(`they logged you as ${p.heard}, so it won't count for you`);
    p.logged = true;
  }
  const q = { auto: auto === true, n: H.log.length + 1, time: new Date(), call: f.call, sent: f.sent, rcvd: f.rcvd, ref: f.ref, ok: !errs.length, errs, trueCall: p ? p.s.call : '', trueRef: p ? p.s.ref : '', heardRight: p ? p.heardRight : false, prog: p ? p.s.prog : huntProg(), band: p ? p.s.band : '20', truth: p ? `${p.s.call} ${p.rcvd} ${p.s.ref}` : '' };
  H.log.push(q);
  if (errs.length) line('', '⚠ Log check: ' + errs.join(' · '), 'bad'); else line('', `✓ Logged correctly. ${H.log.filter(x => x.ok).length} parks hunted.`, 'good');
  ['fCall', 'fRcvd', 'fRef'].forEach(k => { if ($(k)) $(k).value = ''; }); $('fSent').value = '59';
  drawLog(); drawSpots();
  if (q.ok) status('Nice! Stay for the next one, RE-SPOT them to help out, or tune another spot.');
}
function drawHuntLog() {
  const tb = $('vbLogB'); if (!tb) return;
  tb.innerHTML = H.log.slice().reverse().map(q => `<tr class="${q.ok ? 'ok' : 'bad'}"><td>${q.n}</td><td>${q.time.toISOString().slice(11, 16)}</td><td><b>${esc(q.call)}</b></td><td>${esc(q.sent)}</td><td>${esc(q.rcvd)}</td><td>${esc(q.ref)}</td><td>${q.auto ? '🤖 ' : ''}${q.ok ? '✓' : '<span title="' + esc(q.errs.join('; ')) + '">✗ ' + esc(q.truth) + '</span>'}</td><td><button type="button" class="vb-qsl" data-qsl="${q.n}" title="Print a QSL card" aria-label="Print a QSL card for ${esc(q.call)}">🖨</button></td></tr>`).join('');
  const man = H.log.filter(q => !q.auto), n = man.length, ok = man.filter(q => q.ok).length, parks = new Set(H.log.filter(q => q.ok).map(q => q.trueRef)).size;
  const e = $('vbStats'); if (e) e.innerHTML = `<div><b>${parks}</b><span>${PROGNAME[huntProg()] === 'SOTA' ? 'summits' : PROGNAME[huntProg()] === 'KFF' ? 'references' : 'parks'} hunted</span></div><div><b>${n ? Math.round(ok / n * 100) + '%' : '—'}</b><span>logged right (by you)</span></div><div><b>${H.spotsGiven}</b><span>re-spots</span></div><div><b>${H.doubled}</b><span>times you doubled</span></div>`;
}
function huntTalk(p, text) {
  const low = ' ' + text.toLowerCase() + ' ';
  if (/ (negative|no no|wrong|not correct|that's not|correction) /.test(low)) return hNeg();
  if (p.rep || / (qsl|roger|thanks|thank you|73|seventy three|seventy-three) /.test(low)) { if (p.rep) $('fSent').value = p.rep; return hReport(); }
  if (p.kind === 'agn') return hAgain();
  if (p.kind === 'qrt') return hLeave();
  const me = myCall(), runs = (p.runs || []).concat([p.raw || '', p.call || '']);
  if (runs.some(r => r && (r.includes(me) || lev(r, me) <= 2 || (me.endsWith(r) && r.length >= 2)))) return hCall();
  status('Not sure what you meant. In hunt mode say your call, then "QSL, you\'re five nine Kentucky, thanks, 73", "again again", or "negative" + your call.');
}
function huntAdif() {
  const f = (k, v) => v ? `<${k}:${String(v).length}>${v} ` : '';
  return H.log.map(q => { const d = q.time.toISOString(); return f('CALL', q.call) + f('QSO_DATE', d.slice(0, 10).replace(/-/g, '')) + f('TIME_ON', d.slice(11, 16).replace(':', '')) + f('BAND', q.band + 'M') + f('MODE', 'SSB') + f('RST_SENT', q.sent) + f('RST_RCVD', q.rcvd) + f('STATION_CALLSIGN', myCall()) + (q.prog === 'sota' ? f('SOTA_REF', q.ref) : f('SIG', q.prog === 'kff' ? 'WWFF' : 'POTA') + f('SIG_INFO', q.ref)) + (S.p2p && S.ref ? f(S.prog === 'sota' ? 'MY_SOTA_REF' : 'MY_SIG_INFO', S.ref) : '') + f('COMMENT', 'KPC PRACTICE HUNT - NOT A REAL QSO') + '<EOR>'; });
}
function setMode(m) {
  if (run.on || H.on) { S.mode === 'hunt' ? huntStop() : stop(); }
  S.mode = m; save();
  document.body.classList.toggle('vb-hunt', m === 'hunt');
  $('vbModeAct').classList.toggle('on', m !== 'hunt'); $('vbModeHunt').classList.toggle('on', m === 'hunt');
  $('vbModeAct').setAttribute('aria-pressed', m !== 'hunt'); $('vbModeHunt').setAttribute('aria-pressed', m === 'hunt');
  const lh = $('vbLogH'); if (lh) lh.textContent = m === 'hunt' ? 'Your Hunter Log' : 'Your Log';
  const th = $('vbLogStH'); if (th) th.textContent = m === 'hunt' ? 'PARK' : 'ST';
  const fr = $('fRefL'); if (fr) { fr.hidden = m !== 'hunt' && S.prog === 'off'; fr.firstChild.nodeValue = m === 'hunt' ? 'THEIR PARK / REF ' : 'THEIR PARK / REF '; const sm = fr.querySelector('small'); if (sm) sm.textContent = m === 'hunt' ? '(copy it from the air)' : '(only if they give one)'; }
  $('vbBand').innerHTML = ''; status(m === 'hunt' ? 'Hunter mode: press START to load the spots.' : 'Enter your call and press START.');
  drawLog(); drawSpots(); drawTuned();
}

/* ---------------- talk back: push-to-talk + the browser's speech recognition ----------------
   Hold the button (or tap once to start, tap again to stop), say it like on the air. We pull out the call sign
   (phonetics or plain letters), the report, and what you're doing: CQ, QRZ, say again, or thanks/73 to close. */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
const PH = { alpha: 'A', alfa: 'A', bravo: 'B', charlie: 'C', delta: 'D', echo: 'E', foxtrot: 'F', fox: 'F', golf: 'G', hotel: 'H', india: 'I', juliet: 'J', juliett: 'J', kilo: 'K', kilowatt: 'K', king: 'K', lima: 'L', mike: 'M', mexico: 'M', november: 'N', nancy: 'N', oscar: 'O', ocean: 'O', papa: 'P', peter: 'P', quebec: 'Q', queen: 'Q', romeo: 'R', radio: 'R', sierra: 'S', sugar: 'S', tango: 'T', tom: 'T', uniform: 'U', victor: 'V', whiskey: 'W', whisky: 'W', xray: 'X', 'x-ray': 'X', yankee: 'Y', zulu: 'Z', zebra: 'Z', japan: 'J', italy: 'I', canada: 'C', germany: 'G',
  zero: '0', one: '1', won: '1', two: '2', to: '2', too: '2', three: '3', four: '4', for: '4', five: '5', six: '6', seven: '7', eight: '8', nine: '9', niner: '9' };
function parseSpeech(t) {
  const low = ' ' + t.toLowerCase().replace(/[.,!?]/g, ' ').replace(/x ray/g, 'xray').replace(/\s+/g, ' ') + ' ';
  const has = re => re.test(low);
  // call sign: the longest run of phonetics / single letters / digits
  const toks = low.trim().split(' '); let best = '', cur = ''; const runs = [];
  for (const w of toks) {
    const v = PH[w] || (/^[a-z]$/.test(w) ? w.toUpperCase() : /^\d+$/.test(w) && w.length <= 2 ? w : /^[a-z]{1,2}\d[a-z]{1,4}$/.test(w) ? w.toUpperCase() : null);
    if (v) cur += v; else { if (cur) runs.push(cur); if (cur.length > best.length) best = cur; cur = ''; }
  }
  if (cur) runs.push(cur); if (cur.length > best.length) best = cur;
  let call = best.replace(/^(59|5 9)/, '');
  const rep = has(/ (five nine|five by nine|five and nine|fifty nine|fifty-nine|5 9|59|5 by 9) /) ? '59' : has(/ (five eight|five by eight|fifty eight|fifty-eight|58) /) ? '58' : has(/ (five seven|five by seven|fifty seven|fifty-seven|57) /) ? '57' : has(/ (five five|fifty five|fifty-five|55) /) ? '55' : has(/ (four four|forty four|forty-four|44) /) ? '44' : '';
  if (rep && call.endsWith(rep)) call = call.slice(0, -rep.length);
  // ham lingo (speech-to-text writes these many ways)
  const QSL = / (qsl|q s l|q sl|qs l|cue s l|q.s.l|roger|rodger|roger roger|rodger rodger|roger that|copy|copied|copy that|good copy|you'?re in the log|in the log|got you|got it|confirmed) /;
  const QRZ = / (qrz|q r z|q rz|qr z|cue are zee|q r zed|anybody|anyone else|who'?s calling|who is calling|next|any more|anyone|go ahead) /;
  const AGN = / (say again|again again|again|agn agn|repeat|come again|agn|your call again|call again|last two|last letters|fill|didn'?t copy|missed that|one more time|please repeat) /;
  const closing = (has(/ (73|seventy three|seventy-three|seven three|thanks|thank you|thank|tnx) /) || has(QSL)) && !rep;
  const kind = has(/ (qrt|q r t|shutting down|going qrt|signing off|clear and off) /) ? 'qrt' : has(/ (qrx|q r x|stand by|standby|hold on|wait one) /) ? 'qrx'
    : has(/ (cq|c q|seek you|sea queue|calling cq) /) ? 'cq' : closing ? 'close' : has(AGN) && !rep ? 'agn' : has(QRZ) && !rep && (!call || call.length < 4) ? 'qrz'
    : (call || rep) ? 'report' : '';
  return { kind, raw: best, runs, call: /^[A-Z0-9]{3,8}$/.test(call) && /\d/.test(call) ? call : (call.length >= 2 && call.length < 4 ? call : ''), rep };
}
let rec = null, recOn = false, recHeld = 0, recWant = false, recText = '', recOffAt = 0;
/* Keyed = recWant. Chrome ends recognition on its own after a short pause, so while you're still keyed we quietly start it again
   and keep everything you said; the words are only acted on when you unkey. */
function recBegin() {
  rec = new SR(); rec.lang = 'en-US'; rec.interimResults = true; rec.maxAlternatives = 1; rec.continuous = !ANDROID; // Android repeats everything said so far in every result when continuous
  let seg = '';
  rec.onresult = e => { let t = '', f = ''; if (ANDROID) { const r = e.results[e.results.length - 1]; t = r[0].transcript + ' '; if (r.isFinal) f = t; } else for (const r of e.results) { t += r[0].transcript + ' '; if (r.isFinal) f += r[0].transcript + ' '; } seg = f; const l = $('vbHeard'); if (l) { l.textContent = '🎙 ' + (recText + t).trim(); l.classList.add('said'); } rec._last = t; };
  rec.onerror = e => { if (e.error === 'no-speech' || e.error === 'aborted') return; const l = $('vbHeard'); if (l) { l.textContent = e.error === 'not-allowed' ? 'The microphone is blocked: allow it for this site.' : 'Mic problem: ' + e.error; l.classList.add('said'); } if (e.error === 'not-allowed') recWant = false; };
  rec.onend = () => {
    recText += (seg || rec._last || '') + ' ';
    if (recWant) { try { recBegin(); return; } catch (x) {} }
    recOn = false; recOffAt = Date.now(); $('vbTalk').classList.remove('on'); if (run.on) hiss(true);
    const said = recText.replace(/\s+/g, ' ').trim(); recText = '';
    if (said) talkDo(said); else { const l = $('vbHeard'); if (l) { l.textContent = 'Didn\'t hear anything. Hold the button (or tap it once) while you talk.'; l.classList.add('said'); } }
  };
  rec.start();
}
function talkStart() {
  if (!SR || !run.on || recOn) return;
  hush(); run.gen++; recText = ''; recWant = true; if (H.on) H.cut = true;
  try { recBegin(); recOn = true; $('vbTalk').classList.add('on'); hiss(false); } catch (e) { recWant = false; } // like a real rig: the receiver goes quiet while you transmit
}
function talkStop() { recWant = false; if (rec && recOn) try { rec.stop(); } catch (e) {} }
/* the spoken run can pick up stray words ("a", "to", "for"): try every piece of it and keep the one closest to a station that's calling */
function bestSub(runs0) {
  const me = myCall(), list = (Array.isArray(runs0) ? runs0 : [runs0]).map(x => String(x).replace(/^(59|5 9)/, '')).filter(x => x && x !== me);
  const calls = run.callers.map(x => x.call); let best = list.sort((a, b) => b.length - a.length)[0] || '', bd = 99;
  if (!calls.length) return best;
  for (const r0 of list) for (let i = 0; i < r0.length; i++) for (let j = i + 3; j <= Math.min(r0.length, i + 8); j++) {
    const sub = r0.slice(i, j); if (!/\d/.test(sub)) continue;
    const d = Math.min(...calls.map(c => lev(c, sub))) + (r0.length - sub.length) * 0.01;
    if (d < bd) { bd = d; best = sub; }
  }
  return best;
}
async function talkDo(text) {
  text = String(text).replace(/\b((?:\S+\s+){0,5}\S+)(?:\s+\1\b){2,}/gi, '$1'); // a phrase repeated 3+ times (a phone glitch) counts once
  const p = parseSpeech(text);
  const l = $('vbHeard'); if (l) { l.textContent = `🎙 "${text}"`; l.classList.add('said'); }
  if (S.mode === 'hunt') return huntTalk(p, text);
  if (p.kind === 'qrt') { line('YOU', 'QRT, thanks everyone, 73.', 'you'); return stop(); }
  if (p.kind === 'qrx') { hush(); run.gen++; line('YOU', 'QRX, stand by please.', 'you'); status('Standing by. Say "QRZ" or press QRZ? when you\'re ready.'); return; }
  if (p.kind === 'cq') return cq();
  if (p.kind === 'agn') return agn();
  if (p.kind === 'qrz') { if (p.call && p.call.length < 4) $('fCall').value = p.call; return qrz(); }
  if (p.kind === 'close') return say73();
  if (p.kind === 'report') {
    if (p.call && p.call.length < 4) { $('fCall').value = p.call; return qrz(); }
    if (p.call || (p.runs && p.runs.length)) $('fCall').value = bestSub(p.runs && p.runs.length ? p.runs : [p.raw || p.call]); if (p.rep) $('fSent').value = p.rep;
    if (!$('fCall').value) { status('I heard a report but no call sign. Say their call, like "Whiskey Four Alpha Bravo Charlie, five nine Kentucky".'); return; }
    return sendReport({ speech: true });
  }
  status('Not sure what you meant. Try "CQ POTA...", their call + "five nine", "say again", "QRZ" or "thanks, 73".');
}

function init() {
  if (!$('vbGo')) return;
  if (!window.speechSynthesis) { status('This browser has no built-in voices. Try Chrome, Edge or Safari.'); }
  const bind = (id, k, up, num) => { const e = $(id); if (!e) return; e.value = S[k]; e.addEventListener(e.tagName === 'SELECT' || e.type === 'range' ? 'input' : 'input', () => { S[k] = num ? +e.value : up ? e.value.toUpperCase().trim() : e.value; save(); lbl(); }); };
  bind('vbBandSel', 'band'); bind('vbCall', 'call', true); bind('vbSt', 'st'); bind('vbRef', 'ref', true); bind('vbLevel', 'level', false, true); bind('vbVol', 'vol', false, true); bind('vbHiss', 'hiss', false, true); bind('vbRate', 'rate', false, true);
  const lbl = () => { const l = $('vbLevelV'); if (l) l.textContent = `${S.level}: ${LEVELS[S.level].name}`; if (run.on) hiss(true); };
  $('vbLevel').addEventListener('change', () => { lbl(); }); lbl();
  $('vbGo').addEventListener('click', () => S.mode === 'hunt' ? (H.on ? huntStop() : huntStart()) : (run.on ? stop() : start()));
  $('vbModeAct').addEventListener('click', () => setMode('act')); $('vbModeHunt').addEventListener('click', () => setMode('hunt'));
  [['hCall', hCall], ['hRep', hReport], ['hAgn', hAgain], ['hNeg', hNeg], ['hLeave', hLeave]].forEach(([id, fn]) => { const e = $(id); if (e) e.addEventListener('click', fn); });
  $('vbSpots').addEventListener('click', e => { const t = e.target.closest('[data-tune]'); if (t) tune(t.dataset.tune); const r = e.target.closest('[data-respot]'); if (r) respot(r.dataset.respot); });
  const pp = $('vbP2P'); if (pp) { pp.checked = !!S.p2p; pp.addEventListener('change', () => { S.p2p = pp.checked; save(); if (S.p2p && !S.ref) status('Put your park in YOUR PARK so they know where you are.'); }); }
  $('vbCq').addEventListener('click', cq); $('vbQrz').addEventListener('click', qrz); $('vbAgn').addEventListener('click', agn);
  if ($('vbTest')) $('vbTest').addEventListener('click', testVoice);
  if ($('vbSkip')) $('vbSkip').addEventListener('click', skip);
  if ($('vb73')) $('vb73').addEventListener('click', () => say73());
  if ($('vbQsl')) $('vbQsl').addEventListener('click', () => say73('QSL, thank you, 73.'));
  const pg = $('vbProg'); if (pg) { pg.value = S.prog; const lab = () => { const l = $('vbRefL'); if (l) l.firstChild.nodeValue = S.prog === 'sota' ? 'YOUR SUMMIT' : S.prog === 'kff' ? 'YOUR KFF REF' : S.prog === 'off' ? 'YOUR REF (not used)' : 'YOUR PARK'; const fr = $('fRefL'); if (fr) fr.hidden = S.prog === 'off' && S.mode !== 'hunt'; drawLog(); }; pg.addEventListener('change', () => { S.prog = pg.value; save(); lab(); if (H.on) { hLeave(); H.spots = Array.from({ length: 7 }, newSpot); drawSpots(); } }); lab(); }
  const al = $('vbAuto'); if (al) { al.checked = !!S.autolog; al.addEventListener('change', () => { S.autolog = al.checked; save(); }); }
  const mic = $('vbMic'), micSync = () => { const t = $('vbTalk'); if (t) t.hidden = !S.mic; const h = $('vbHeard'); if (h) h.hidden = !S.mic; if (mic) mic.checked = !!S.mic; document.body.classList.toggle('vb-nomic', !S.mic); };
  if (mic) mic.addEventListener('change', () => { S.mic = mic.checked; save(); micSync(); }); micSync();
  const tb = $('vbTalk');
  if (tb) {
    if (!SR) { tb.disabled = true; tb.textContent = '🎙 TALKING BACK NEEDS CHROME, EDGE OR ANDROID'; }
    else {
      // hold to talk; a quick tap toggles instead
      tb.addEventListener('pointerdown', e => { e.preventDefault(); try { tb.setPointerCapture(e.pointerId); } catch (x) {} if (recOn) { talkStop(); return; } recHeld = Date.now(); talkStart(); });
      tb.addEventListener('pointerup', () => { if (recOn && Date.now() - recHeld > 450) talkStop(); });
      tb.addEventListener('contextmenu', e => e.preventDefault());
      document.addEventListener('keydown', e => { if (e.code === 'Space' && S.mic && !/INPUT|TEXTAREA|SELECT/.test(e.target.tagName) && run.on && !e.repeat) { e.preventDefault(); recHeld = Date.now(); talkStart(); } });
      document.addEventListener('keyup', e => { if (e.code === 'Space' && recOn) talkStop(); });
    }
  }
  $('vbLogB').addEventListener('click', e => { const b = e.target.closest('[data-qsl]'); if (b) qslPrint(+b.dataset.qsl); });
  $('vbSend').addEventListener('click', sendReport); $('vbLog').addEventListener('click', logIt); $('vbAdif').addEventListener('click', adif);
  // keyboard: Enter in CALL = send report, Enter in STATE = log it; F1 CQ, F2 QRZ, F3 AGN
  $('fCall').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); if (S.mode !== 'hunt') sendReport(); $('fRcvd').focus(); } });
  ['fRcvd', 'fSt', 'fRef'].forEach(id => $(id).addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); logIt(); } }));
  document.addEventListener('keydown', e => { const m = S.mode === 'hunt' ? { F1: hCall, F2: hReport, F3: hAgain, F4: hNeg, F6: hLeave }[e.key] : { F1: cq, F2: qrz, F3: agn, F4: skip, F5: () => say73(), F6: () => say73('QSL, thank you, 73.') }[e.key]; if (m && run.on) { e.preventDefault(); m(); } });
  form(false); setMode(S.mode === 'hunt' ? 'hunt' : 'act');
}
window.KPCSSB = { H, tune, hCall, hReport, hNeg, huntLog, setMode, run, S, say1, check, lev, parseSpeech, talkDo, bestSub, skip, say73 };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
