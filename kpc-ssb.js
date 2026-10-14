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
function loadVoices() { const v = (window.speechSynthesis && speechSynthesis.getVoices()) || []; VO = v.filter(x => /^en[-_]/i.test(x.lang)); if (!VO.length) VO = v; }
if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }
function speak(text, who) {
  return new Promise(res => {
    if (!window.speechSynthesis) { res(); return; }
    const u = new SpeechSynthesisUtterance(text);
    if (who && VO.length) u.voice = VO[who.vi % VO.length];
    u.rate = who ? who.rate : 1; u.pitch = who ? who.pitch : 1; u.volume = Math.max(0.15, Math.min(1, (who ? who.vol : 1) * S.vol));
    let done = false; const fin = () => { if (!done) { done = true; clearTimeout(tm); res(); } };
    const tm = setTimeout(fin, 1500 + text.length * 95 / u.rate); // some browsers never fire 'end'
    u.onend = u.onerror = fin;
    speechSynthesis.speak(u);
  });
}
function hush() { if (window.speechSynthesis) speechSynthesis.cancel(); }

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
    nG.gain.setTargetAtTime(on ? S.hiss * 0.25 : 0, AC.currentTime, 0.2);
  } catch (e) {}
}

/* ---------------- state ---------------- */
const S = Object.assign({ call: '', st: 'KY', ref: '', level: 1, vol: 0.9, hiss: 0.3, rate: 1 }, store.get('kpcSSB', {}));
const save = () => store.set('kpcSSB', S);
const run = { on: false, callers: [], cur: null, sent: false, last: '', log: [], t0: 0, gen: 0, worked: new Set() };
const myCall = () => (S.call || '').toUpperCase().trim();

function status(t) { const e = $('vbStatus'); if (e) e.textContent = t; }
function line(who, text, cls) { const b = $('vbBand'); if (!b) return; const d = document.createElement('div'); d.className = 'vb-line ' + (cls || ''); d.innerHTML = `<b>${esc(who)}</b> ${esc(text)}`; b.appendChild(d); b.scrollTop = b.scrollHeight; while (b.children.length > 120) b.removeChild(b.firstChild); }
function showText() { return $('vbShow') && $('vbShow').checked; }

function arrivals() {
  const lv = LEVELS[S.level] || LEVELS[1], want = rnd(lv.n[0], lv.n[1]);
  while (run.callers.length < want) {
    const st = pick(NEAR); let c; do { c = newCall(st); } while (run.worked.has(c) || run.callers.some(x => x.call === c) || c === myCall());
    run.callers.push({ call: c, st, rst: pick(['59', '59', '59', '57', '58', '55', '44']), vi: rnd(0, 50), rate: (0.95 + Math.random() * 0.35) * S.rate, pitch: 0.8 + Math.random() * 0.5, vol: 0.55 + Math.random() * 0.45 });
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
  hush(); run.gen++; Object.assign(run, { on: true, callers: [], cur: null, sent: false, t0: Date.now() });
  hiss(true); $('vbGo').textContent = '■ STOP'; $('vbGo').classList.add('stop');
  status(`Level ${S.level}: ${LEVELS[S.level].name}. Call CQ to start.`);
  form(true);
}
function stop() { hush(); run.gen++; run.on = false; hiss(false); $('vbGo').textContent = '▶ START'; $('vbGo').classList.remove('stop'); status('Stopped.'); form(false); }
function form(on) { ['vbCq', 'vbQrz', 'vbAgn', 'vbSend', 'vbLog'].forEach(id => { const e = $(id); if (e) e.disabled = !on; }); }

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
async function sendReport() {
  if (!run.on) return;
  const c = ($('fCall').value || '').toUpperCase().trim(), rs = ($('fSent').value || '59').trim();
  if (!c) { status('Type the call you heard in the CALL box first.'); $('fCall').focus(); return; }
  hush(); run.gen++;
  line('YOU', `${c}, you're ${rs} ${STN[S.st] || S.st}${S.ref ? ', park ' + S.ref : ''}. ${myCall()}.`, 'you');
  let o = run.callers.find(x => x.call === c);
  if (!o) {
    const near = run.callers.find(x => lev(x.call, c) <= 2);
    if (near) { run.cur = near; run.sent = true; if (showText()) line(near.call, `Negative, ${near.call}`, 'them'); await speak(`Negative. ${say1(near.call)}. ${say1(near.call)}.`, near); status('They corrected you. Fix the CALL box (no penalty yet, but it counts if you log it wrong).'); return; }
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
async function logIt() {
  if (!run.on) return;
  const f = { call: ($('fCall').value || '').toUpperCase().trim(), sent: ($('fSent').value || '59').trim(), rcvd: ($('fRcvd').value || '').trim(), st: ($('fSt').value || '').toUpperCase().trim() };
  const o = run.cur && run.sent ? run.cur : run.callers.find(x => x.call === f.call);
  if (!f.call) { status('Nothing to log yet.'); return; }
  const errs = o ? check(o, f) : [`${f.call} never called you`];
  const q = { n: run.log.length + 1, time: new Date(), call: f.call, sent: f.sent, rcvd: f.rcvd, st: f.st, ok: !errs.length, errs, secs: o && o.t0 ? Math.round((Date.now() - o.t0) / 1000) : 0, truth: o ? `${o.call} ${o.rst} ${o.st}` : '' };
  run.log.push(q); drawLog();
  hush(); run.gen++;
  line('YOU', `Thanks, 73. QRZ? ${myCall()}`, 'you');
  if (errs.length) line('', '⚠ Log check: ' + errs.join(' · '), 'bad'); else line('', '✓ Logged correctly.', 'good');
  if (o) {
    run.callers = run.callers.filter(x => x !== o); run.worked.add(o.call);
    // they sign too: "thanks, 73"
    const g = run.gen, bye = pick(['Thanks, seventy-three!', 'Seventy-three, thanks for the park!', 'Thank you, seventy-three.', 'Thanks for the contact, seventy-three.']);
    if (showText()) line(o.call, bye.replace(/seventy-three/gi, '73'), 'them');
    await speak(bye, o); if (g !== run.gen) return;
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

function init() {
  if (!$('vbGo')) return;
  if (!window.speechSynthesis) { status('This browser has no built-in voices. Try Chrome, Edge or Safari.'); }
  const bind = (id, k, up, num) => { const e = $(id); if (!e) return; e.value = S[k]; e.addEventListener(e.tagName === 'SELECT' || e.type === 'range' ? 'input' : 'input', () => { S[k] = num ? +e.value : up ? e.value.toUpperCase().trim() : e.value; save(); lbl(); }); };
  bind('vbCall', 'call', true); bind('vbSt', 'st'); bind('vbRef', 'ref', true); bind('vbLevel', 'level', false, true); bind('vbVol', 'vol', false, true); bind('vbHiss', 'hiss', false, true); bind('vbRate', 'rate', false, true);
  const lbl = () => { const l = $('vbLevelV'); if (l) l.textContent = `${S.level}: ${LEVELS[S.level].name}`; if (run.on) hiss(true); };
  $('vbLevel').addEventListener('change', () => { lbl(); }); lbl();
  $('vbGo').addEventListener('click', () => run.on ? stop() : start());
  $('vbCq').addEventListener('click', cq); $('vbQrz').addEventListener('click', qrz); $('vbAgn').addEventListener('click', agn);
  $('vbSend').addEventListener('click', sendReport); $('vbLog').addEventListener('click', logIt); $('vbAdif').addEventListener('click', adif);
  // keyboard: Enter in CALL = send report, Enter in STATE = log it; F1 CQ, F2 QRZ, F3 AGN
  $('fCall').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); sendReport(); $('fRcvd').focus(); } });
  ['fRcvd', 'fSt'].forEach(id => $(id).addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); logIt(); } }));
  document.addEventListener('keydown', e => { const m = { F1: cq, F2: qrz, F3: agn }[e.key]; if (m && run.on) { e.preventDefault(); m(); } });
  form(false); drawLog();
}
window.KPCSSB = { run, S, say1, check, lev };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
