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
  return new Promise(r0 => setTimeout(r0, gap)).then(() => speakNow(text, who));
}
function speakNow(text, who) {
  return new Promise(res => {
    if (!window.speechSynthesis) { res(); return; }
    if (speechSynthesis.paused) speechSynthesis.resume();
    const u = new SpeechSynthesisUtterance(text);
    if (!VO.length) loadVoices();
    if (who && VO.length) {
      // pick a man's or woman's voice when the device has both; otherwise the pitch does the work
      const MALE = /\b(male|man|david|mark|guy|daniel|fred|alex|tom|aaron|arthur|george|james|rishi|eddy|reed|ralph|bruce|junior|lee|oliver|thomas)\b/i;
      const pool = VO.filter(v => who.m ? MALE.test(v.name) : !MALE.test(v.name));
      const list = pool.length ? pool : VO; u.voice = list[who.vi % list.length]; u.lang = u.voice.lang;
    } else u.lang = 'en-US';
    u.rate = who ? who.rate : 1; u.pitch = who ? who.pitch : 1; u.volume = Math.max(0.15, Math.min(1, (who ? who.vol : 1) * S.vol));
    let done = false; const fin = () => { if (!done) { done = true; clearTimeout(tm); res(); } };
    const tm = setTimeout(fin, 1500 + text.length * 95 / u.rate); // some browsers never fire 'end'
    u.onend = fin; u.onerror = e => { lastErr = (e && e.error) || 'error'; if (lastErr !== 'interrupted' && lastErr !== 'canceled' && Date.now() - lastCancel > 400) { const d = $('vbDiag'); if (d) d.textContent = 'Voice problem: ' + lastErr + '. Tap TEST VOICE to check.'; } fin(); };
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
  setTimeout(() => speakNow('Kilo Zulu Four Charlie Papa, you are five nine, Kentucky.', VO.length ? { vi: 0, rate: 1, pitch: 1, vol: 1 } : null), 900);
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
const S = Object.assign({ call: '', st: 'KY', ref: '', level: 1, vol: 0.9, hiss: 0.3, rate: 1, mic: true }, store.get('kpcSSB', {}));
const save = () => store.set('kpcSSB', S);
const run = { on: false, callers: [], cur: null, sent: false, last: '', log: [], t0: 0, gen: 0, worked: new Set() };
const myCall = () => (S.call || '').toUpperCase().trim() || 'K4TEST';

function status(t) { const e = $('vbStatus'); if (e) e.textContent = t; }
function line(who, text, cls) { const b = $('vbBand'); if (!b) return; const d = document.createElement('div'); d.className = 'vb-line ' + (cls || ''); d.innerHTML = `<b>${esc(who)}</b> ${esc(text)}`; b.appendChild(d); b.scrollTop = b.scrollHeight; while (b.children.length > 120) b.removeChild(b.firstChild); }
function showText() { return $('vbShow') && $('vbShow').checked; }

function arrivals() {
  const lv = LEVELS[S.level] || LEVELS[1], want = rnd(lv.n[0], lv.n[1]);
  while (run.callers.length < want) {
    const st = pick(NEAR); let c; do { c = newCall(st); } while (run.worked.has(c) || run.callers.some(x => x.call === c) || c === myCall());
    run.callers.push({ call: c, st, rst: pick(['59', '59', '59', '57', '58', '55', '44']), vi: rnd(0, 50), rate: (0.95 + Math.random() * 0.35) * S.rate, vol: 0.55 + Math.random() * 0.45 }); { const o = run.callers[run.callers.length - 1]; o.m = Math.random() < 0.65; o.pitch = o.m ? 0.5 + Math.random() * 0.3 : 1 + Math.random() * 0.3; }
  }
}
async function callIn(list) {
  const g = run.gen; run.last = '';
  for (const o of list) {
    if (g !== run.gen) return;
    const twice = chance(S.level >= 3 ? 0.25 : 0.5);
    const t = (o.p2p ? 'park to park, ' : '') + say1(o.call) + (twice ? ', ' + say1(o.call) : '');
    if (showText()) line(o.call, (o.p2p ? 'P2P ' : '') + o.call + (twice ? ' ' + o.call : ''), 'them');
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
function form(on) { ['vbCq', 'vbQrz', 'vbAgn', 'vbSend', 'vbLog', 'vbTalk', 'vbSkip', 'vb73'].forEach(id => { const e = $(id); if (e) e.disabled = !on; }); }

async function cq() {
  if (!run.on) return;
  hush(); run.gen++;
  line('YOU', `CQ POTA, CQ POTA, this is ${myCall()} ${say1(myCall())}, ${myCall()} portable in a park.`, 'you');
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
  line('YOU', 'Say again?', 'you');
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
  line('YOU', `${c}, you're ${rs} ${STN[S.st] || S.st}${S.ref ? ', park ' + S.ref : ''}. ${myCall()}.`, 'you');
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
  const t = again ? `You're ${say1(o.rst)}, ${st}. ${st}.` : pick([`Thanks! You're ${say1(o.rst)} ${say1(o.rst)}, ${st}, ${st}. ${o.p2p ? 'Park to park from ' + say1(o.park || 'US') + '.' : ''}`, `Roger, thank you. ${say1(o.rst)} into ${st}. Thanks for the park.`, `Good copy. You're ${say1(o.rst)}, ${st}.`]);
  if (showText()) line(o.call, t.replace(/[A-Za-z-]+ (?=[A-Za-z-]+ )/g, m => m), 'them'); else line(o.call.slice(0, 0) + '📢', 'they give you their report and state', 'them');
  if (g !== run.gen) return;
  await speak(t, o);
  status('Log their report and state, then press LOG IT (you say "thanks, 73, QRZ").');
}
function check(o, f) {
  const errs = [];
  if (f.call !== o.call) errs.push(`call: you logged ${f.call || '(blank)'}, it was ${o.call}`);
  if (f.rcvd.replace(/\D/g, '') !== o.rst) errs.push(`their report: you logged ${f.rcvd || '(blank)'}, they gave ${o.rst}`);
  const stOk = f.st === o.st || (STN[o.st] || '').toUpperCase() === f.st;
  if (!stOk) errs.push(`state: you logged ${f.st || '(blank)'}, it was ${o.st} (${STN[o.st]})`);
  return errs;
}
const sayBye = o => { const bye = pick(['Thanks, seventy-three!', 'Seventy-three, thanks for the park!', 'Thank you, seventy-three.', 'Thanks for the contact, seventy-three.']); if (showText()) line(o.call, bye.replace(/seventy-three/gi, '73'), 'them'); return speak(bye, o); };
/* you said "thanks, 73" on the mic: they sign too, but YOU still do the logging (that's the skill we're practicing) */
async function say73() {
  if (!run.on) return;
  const o = run.cur && run.sent ? run.cur : null;
  hush(); run.gen++; line('YOU', 'Thanks, 73.', 'you');
  if (!o) { status('Thanks, 73! Nobody to sign with right now. Call CQ or QRZ.'); return; }
  o.signed = true; const g = run.gen; await sayBye(o); if (g !== run.gen) return;
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
  ['fCall', 'fRcvd', 'fSt'].forEach(id => { $(id).value = ''; }); $('fSent').value = '59';
  if (chance(0.6)) arrivals();
  if (run.callers.length) { await new Promise(r0 => setTimeout(r0, 300)); await callIn(run.callers.slice()); } else status('Nobody calling. Call CQ again.');
}
async function logIt() {
  if (!run.on) return;
  const f = { call: ($('fCall').value || '').toUpperCase().trim(), sent: ($('fSent').value || '59').trim(), rcvd: ($('fRcvd').value || '').trim(), st: ($('fSt').value || '').toUpperCase().trim() };
  const o = run.cur && run.sent ? run.cur : run.callers.find(x => x.call === f.call);
  if (!f.call) { status('Nothing to log yet.'); return; }
  const errs = o ? check(o, f) : [`${f.call} never called you`];
  const q = { n: run.log.length + 1, time: new Date(), call: f.call, sent: f.sent, rcvd: f.rcvd, st: f.st, ok: !errs.length, errs, secs: o && o.t0 ? Math.round((Date.now() - o.t0) / 1000) : 0, truth: o ? `${o.call} ${o.rst} ${o.st}` : '' };
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
  ['fCall', 'fRcvd', 'fSt'].forEach(id => { $(id).value = ''; }); $('fSent').value = '59'; $('fCall').focus();
  if (chance(0.6)) arrivals();
  if (run.callers.length) { await new Promise(r => setTimeout(r, 400)); await callIn(run.callers.slice()); }
  else status('Nobody calling. Call CQ again.');
  const good = run.log.filter(x => x.ok).length;
  if (good && good % 10 === 0 && S.level < 5 && run.log.slice(-10).every(x => x.ok)) { status(`10 clean contacts in a row! Try level ${S.level + 1}.`); }
}
function drawLog() {
  const tb = $('vbLogB'); if (!tb) return;
  tb.innerHTML = run.log.slice().reverse().map(q => `<tr class="${q.ok ? 'ok' : 'bad'}"><td>${q.n}</td><td>${q.time.toISOString().slice(11, 16)}</td><td><b>${esc(q.call)}</b></td><td>${esc(q.sent)}</td><td>${esc(q.rcvd)}</td><td>${esc(q.st)}</td><td>${q.ok ? '✓' : '<span title="' + esc(q.errs.join('; ')) + '">✗ ' + esc(q.truth) + '</span>'}</td></tr>`).join('');
  const n = run.log.length, ok = run.log.filter(q => q.ok).length, mins = Math.max(1, (Date.now() - run.t0) / 60000);
  const e = $('vbStats'); if (e) e.innerHTML = `<div><b>${n}</b><span>contacts</span></div><div><b>${n ? Math.round(ok / n * 100) : 0}%</b><span>logged right</span></div><div><b>${Math.round(n / mins * 60)}</b><span>per hour</span></div>`;
}
function adif() {
  if (!run.log.length) return;
  const f = (k, v) => v ? `<${k}:${String(v).length}>${v} ` : '';
  const rows = run.log.map(q => { const d = q.time.toISOString(); return f('CALL', q.call) + f('QSO_DATE', d.slice(0, 10).replace(/-/g, '')) + f('TIME_ON', d.slice(11, 16).replace(':', '')) + f('BAND', '20M') + f('MODE', 'SSB') + f('RST_SENT', q.sent) + f('RST_RCVD', q.rcvd) + f('STATE', q.st) + f('STATION_CALLSIGN', myCall()) + f('MY_SIG', S.ref ? 'POTA' : '') + f('MY_SIG_INFO', S.ref) + f('COMMENT', 'KPC PRACTICE - NOT A REAL QSO') + '<EOR>'; });
  const txt = 'KPC Voice Pileup Practice log (PRACTICE ONLY - do not upload to POTA)\n<ADIF_VER:5>3.1.4 <PROGRAMID:3>KPC <EOH>\n' + rows.join('\n') + '\n';
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([txt], { type: 'text/plain' })); a.download = `KPC-practice-${myCall() || 'log'}.adi`; a.click();
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
let rec = null, recOn = false, recHeld = 0, recWant = false, recText = '';
/* Keyed = recWant. Chrome ends recognition on its own after a short pause, so while you're still keyed we quietly start it again
   and keep everything you said; the words are only acted on when you unkey. */
function recBegin() {
  rec = new SR(); rec.lang = 'en-US'; rec.interimResults = true; rec.maxAlternatives = 1; rec.continuous = true;
  let seg = '';
  rec.onresult = e => { let t = '', f = ''; for (const r of e.results) { t += r[0].transcript + ' '; if (r.isFinal) f += r[0].transcript + ' '; } seg = f; const l = $('vbHeard'); if (l) { l.textContent = '🎙 ' + (recText + t).trim(); l.classList.add('said'); } rec._last = t; };
  rec.onerror = e => { if (e.error === 'no-speech' || e.error === 'aborted') return; const l = $('vbHeard'); if (l) { l.textContent = e.error === 'not-allowed' ? 'The microphone is blocked: allow it for this site.' : 'Mic problem: ' + e.error; l.classList.add('said'); } if (e.error === 'not-allowed') recWant = false; };
  rec.onend = () => {
    recText += (seg || rec._last || '') + ' ';
    if (recWant) { try { recBegin(); return; } catch (x) {} }
    recOn = false; $('vbTalk').classList.remove('on'); if (run.on) hiss(true);
    const said = recText.replace(/\s+/g, ' ').trim(); recText = '';
    if (said) talkDo(said); else { const l = $('vbHeard'); if (l) { l.textContent = 'Didn\'t hear anything. Hold the button (or tap it once) while you talk.'; l.classList.add('said'); } }
  };
  rec.start();
}
function talkStart() {
  if (!SR || !run.on || recOn) return;
  hush(); run.gen++; recText = ''; recWant = true;
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
  const p = parseSpeech(text);
  const l = $('vbHeard'); if (l) { l.textContent = `🎙 "${text}"`; l.classList.add('said'); }
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
  bind('vbCall', 'call', true); bind('vbSt', 'st'); bind('vbRef', 'ref', true); bind('vbLevel', 'level', false, true); bind('vbVol', 'vol', false, true); bind('vbHiss', 'hiss', false, true); bind('vbRate', 'rate', false, true);
  const lbl = () => { const l = $('vbLevelV'); if (l) l.textContent = `${S.level}: ${LEVELS[S.level].name}`; if (run.on) hiss(true); };
  $('vbLevel').addEventListener('change', () => { lbl(); }); lbl();
  $('vbGo').addEventListener('click', () => run.on ? stop() : start());
  $('vbCq').addEventListener('click', cq); $('vbQrz').addEventListener('click', qrz); $('vbAgn').addEventListener('click', agn);
  if ($('vbTest')) $('vbTest').addEventListener('click', testVoice);
  if ($('vbSkip')) $('vbSkip').addEventListener('click', skip);
  if ($('vb73')) $('vb73').addEventListener('click', say73);
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
  $('vbSend').addEventListener('click', sendReport); $('vbLog').addEventListener('click', logIt); $('vbAdif').addEventListener('click', adif);
  // keyboard: Enter in CALL = send report, Enter in STATE = log it; F1 CQ, F2 QRZ, F3 AGN
  $('fCall').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); sendReport(); $('fRcvd').focus(); } });
  ['fRcvd', 'fSt'].forEach(id => $(id).addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); logIt(); } }));
  document.addEventListener('keydown', e => { const m = { F1: cq, F2: qrz, F3: agn, F4: skip, F5: say73 }[e.key]; if (m && run.on) { e.preventDefault(); m(); } });
  form(false); drawLog();
}
window.KPCSSB = { run, S, say1, check, lev, parseSpeech, talkDo, bestSub, skip, say73 };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
