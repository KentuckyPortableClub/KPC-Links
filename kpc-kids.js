/* KPC Kids Radio Zone: phonetic alphabet games. Nothing about the player is stored except stars on this device. */
(function () {
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1)), pick = a => a[Math.floor(Math.random() * a.length)];
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const NATO = { A: 'Alpha', B: 'Bravo', C: 'Charlie', D: 'Delta', E: 'Echo', F: 'Foxtrot', G: 'Golf', H: 'Hotel', I: 'India', J: 'Juliett', K: 'Kilo', L: 'Lima', M: 'Mike', N: 'November', O: 'Oscar', P: 'Papa', Q: 'Quebec', R: 'Romeo', S: 'Sierra', T: 'Tango', U: 'Uniform', V: 'Victor', W: 'Whiskey', X: 'X-ray', Y: 'Yankee', Z: 'Zulu',
  '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four', '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine' };
const EMO = { A: '✈️', B: '👏', C: '🧸', D: '🔺', E: '🔊', F: '🦊', G: '⛳', H: '🏨', I: '🇮🇳', J: '🌙', K: '⚖️', L: '🏔️', M: '🎤', N: '🍂', O: '🏆', P: '👨', Q: '🍁', R: '🌹', S: '⛰️', T: '💃', U: '👕', V: '🏅', W: '🌬️', X: '🩻', Y: '⚾', Z: '🐘' };
const LETTERS = Object.keys(NATO).filter(k => /[A-Z]/.test(k));
let stars = 0; try { stars = +localStorage.getItem('kpcKidsStars') || 0; } catch (e) {}
function addStar(n) { stars += n || 1; try { localStorage.setItem('kpcKidsStars', String(stars)); } catch (e) {} showStars(); }
const BADGES = [[10, '🌟', 'Radio Rookie'], [30, '🎙️', 'Phonetics Pro'], [60, '🕵️', 'Call Sign Detective'], [100, '🏆', 'Radio Ace']];
function showStars() {
  const e = $('kzStars'); if (e) e.textContent = stars;
  const b = $('kzBadges'); if (b) b.innerHTML = BADGES.map(x => `<span class="kz-badge${stars >= x[0] ? ' on' : ''}" title="${x[0]} stars">${x[1]}<small>${x[2]}</small></span>`).join('');
}

/* voices */
let VO = [];
const loadV = () => { const v = (window.speechSynthesis && speechSynthesis.getVoices()) || []; VO = v.filter(x => /^en[-_]/i.test(x.lang)); if (/Android/i.test(navigator.userAgent)) { const l = VO.filter(x => x.localService); if (l.length) VO = l; } };
if (window.speechSynthesis) { loadV(); speechSynthesis.onvoiceschanged = loadV; }
let lastCancel = 0;
function hush() { if (window.speechSynthesis) { speechSynthesis.cancel(); lastCancel = Date.now(); } }
function say(text, rate) {
  return new Promise(res => {
    if (!window.speechSynthesis) { res(); return; }
    setTimeout(() => {
      const u = new SpeechSynthesisUtterance(text); if (VO[0]) { u.voice = VO[0]; u.lang = VO[0].lang; } else u.lang = 'en-US';
      u.rate = rate || 0.9; let done = false; const fin = () => { if (!done) { done = true; res(); } };
      setTimeout(fin, 1500 + text.length * 110 / u.rate); u.onend = u.onerror = fin; speechSynthesis.speak(u);
    }, Math.max(0, 150 - (Date.now() - lastCancel)));
  });
}

/* ---------- Game 1: Phonetic Match ---------- */
const g1 = { mode: 'see', ans: '', streak: 0 };
function g1New() {
  const L = pick(LETTERS); g1.ans = L;
  const wrong = shuffle(LETTERS.filter(x => x !== L)).slice(0, 3), opts = shuffle([L].concat(wrong));
  const q = $('g1Q'), o = $('g1Opts'), f = $('g1Fb'); f.textContent = '';
  if (g1.mode === 'see') {
    q.innerHTML = `<b class="kz-big">${L}</b><span class="dim">Which word is this letter?</span>`;
    o.innerHTML = opts.map(x => `<button type="button" class="kz-opt" data-a="${x}">${EMO[x] || ''} ${NATO[x]}</button>`).join('');
  } else {
    q.innerHTML = `<button type="button" class="kz-btn" id="g1Hear">🔊 HEAR THE WORD</button><span class="dim">Tap the letter you hear.</span>`;
    o.innerHTML = opts.map(x => `<button type="button" class="kz-opt big" data-a="${x}">${x}</button>`).join('');
    $('g1Hear').addEventListener('click', () => { hush(); say(NATO[L]); });
    hush(); say(NATO[L]);
  }
  o.querySelectorAll('.kz-opt').forEach(b => b.addEventListener('click', () => g1Pick(b)));
}
function g1Pick(b) {
  const ok = b.dataset.a === g1.ans, f = $('g1Fb');
  b.classList.add(ok ? 'ok' : 'no');
  if (ok) { g1.streak++; addStar(); f.innerHTML = `<b class="good">⭐ Yes! ${g1.ans} is ${NATO[g1.ans]}.</b>${g1.streak % 5 === 0 ? ` <span>🔥 ${g1.streak} in a row!</span>` : ''}`; hush(); say(`${NATO[g1.ans]}! Great job.`); setTimeout(g1New, 1300); }
  else { g1.streak = 0; f.innerHTML = `<b class="bad">Try again!</b>`; }
}

/* ---------- Game 2: Spell Your Name ---------- */
let g2gen = 0;
async function g2Go() {
  const t = ($('g2In').value || '').toUpperCase().replace(/[^A-Z0-9 ]/g, '').trim(); if (!t) return;
  const out = $('g2Out'), gen = ++g2gen;
  out.innerHTML = t.split('').map((c, i) => c === ' ' ? '<span class="kz-sp"></span>' : `<span class="kz-chip" id="g2c${i}"><b>${c}</b><small>${esc(NATO[c] || c)}</small></span>`).join('');
  hush();
  for (let i = 0; i < t.length; i++) {
    if (gen !== g2gen) return; const c = t[i]; if (c === ' ') continue;
    const el = $('g2c' + i); if (el) el.classList.add('on');
    await say(NATO[c] || c, 0.85);
    if (el) el.classList.remove('on');
  }
  if (gen === g2gen) { addStar(); $('g2Fb').innerHTML = '<b class="good">⭐ Now YOU say it out loud, just like a ham on the radio!</b>'; }
}

/* ---------- Game 3: Call Sign Detective ---------- */
const g3 = { lvl: 1, ans: '', tries: 0 };
function g3Call() {
  const L = () => pick(LETTERS), p = pick(['K', 'W', 'N']), d = String(rnd(0, 9));
  if (g3.lvl === 1) return p + d + L() + L();
  if (g3.lvl === 2) return p + d + L() + L() + L();
  return p + L() + d + L() + L() + L();
}
async function g3New() {
  g3.ans = g3Call(); g3.tries = 0; $('g3In').value = ''; $('g3Fb').textContent = ''; $('g3In').focus({ preventScroll: true });
  await g3Play();
}
async function g3Play() { hush(); await say(g3.ans.split('').map(c => NATO[c]).join(', '), [0, 0.8, 0.9, 1.05][g3.lvl]); }
function g3Check() {
  const got = ($('g3In').value || '').toUpperCase().replace(/[^A-Z0-9]/g, ''), f = $('g3Fb');
  if (!got || !g3.ans) return;
  if (got === g3.ans) { addStar(g3.lvl); f.innerHTML = `<b class="good">🕵️ Case solved! It was ${g3.ans}. +${g3.lvl} ⭐</b>`; hush(); say('Correct! Nice detective work.'); setTimeout(g3New, 1800); }
  else { g3.tries++; const hint = g3.ans.split('').map((c, i) => got[i] === c ? c : '_').join(' '); f.innerHTML = `<b class="bad">Not quite.</b> <span>What you got right: <code>${hint}</code></span>${g3.tries >= 2 ? ` <span>The answer was <b>${g3.ans}</b>.</span>` : ''}`; if (g3.tries >= 2) setTimeout(g3New, 2600); }
}

/* ---------- Morse Code Fun (simple, for kids) ---------- */
const MC = { A:'.-',B:'-...',C:'-.-.',D:'-..',E:'.',F:'..-.',G:'--.',H:'....',I:'..',J:'.---',K:'-.-',L:'.-..',M:'--',N:'-.',O:'---',P:'.--.',Q:'--.-',R:'.-.',S:'...',T:'-',U:'..-',V:'...-',W:'.--',X:'-..-',Y:'-.--',Z:'--..',
  '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.' };
const MD = {}; Object.keys(MC).forEach(k => { MD[MC[k]] = k; });
const EASY = ['E', 'T', 'I', 'M', 'A', 'N', 'S', 'O'];
const dd = code => code.split('').map(c => c === '.' ? '<i class="dot"></i>' : '<i class="dash"></i>').join('');
let AC = null, osc = null, gn = null;
function ac() {
  if (!AC) { AC = new (window.AudioContext || window.webkitAudioContext)(); osc = AC.createOscillator(); osc.frequency.value = 600; gn = AC.createGain(); gn.gain.value = 0; osc.connect(gn); gn.connect(AC.destination); osc.start(); }
  if (AC.state === 'suspended') AC.resume(); return AC;
}
const U = 0.11; // seconds per dit: slow and friendly (about 11 WPM)
let mgen = 0;
function beepSeq(text, onChar) { // plays text; calls onChar(index) as each character starts
  ac(); const g = ++mgen, t0 = AC.currentTime + 0.1; let t = t0; const starts = [];
  gn.gain.cancelScheduledValues(AC.currentTime); gn.gain.setValueAtTime(0, AC.currentTime);
  text.split('').forEach((ch, i) => {
    if (ch === ' ') { t += U * 4; return; }
    const c = MC[ch]; if (!c) return; starts.push([i, t]);
    c.split('').forEach((e, k) => { const d = e === '.' ? U : 3 * U; gn.gain.setTargetAtTime(0.5, t, 0.004); gn.gain.setTargetAtTime(0, t + d, 0.004); t += d + (k < c.length - 1 ? U : 0); });
    t += U * 3;
  });
  if (onChar) starts.forEach(([i, ts]) => setTimeout(() => { if (g === mgen) onChar(i); }, (ts - AC.currentTime) * 1000));
  return new Promise(r => setTimeout(() => r(g === mgen), (t - AC.currentTime) * 1000 + 100));
}
const m4 = { mode: 'name', ans: '', g: 0, key: { down: 0, code: '', timer: 0 } };
const later = (f, ms) => { const g = m4.g; setTimeout(() => { if (g === m4.g) f(); }, ms); };
function m4Draw() {
  const b = $('m4Body'); if (!b) return; m4.g++;
  if (m4.mode === 'name') {
    b.innerHTML = `<input type="text" id="m4In" maxlength="12" autocomplete="off" spellcheck="false" placeholder="Your name" aria-label="Your name"><button type="button" class="kz-btn" id="m4Go">🔊 BEEP MY NAME</button><div class="kz-out" id="m4Out"></div><div class="kz-fb" id="m4Fb"></div>`;
    const go = async () => {
      const t = ($('m4In').value || '').toUpperCase().replace(/[^A-Z0-9 ]/g, '').trim(); if (!t) return;
      $('m4Out').innerHTML = t.split('').map((c, i) => c === ' ' ? '<span class="kz-sp"></span>' : `<span class="kz-chip mc" id="m4c${i}"><b>${c}</b><small>${dd(MC[c] || '')}</small></span>`).join('');
      const ok = await beepSeq(t, i => { document.querySelectorAll('#m4Out .on').forEach(e => e.classList.remove('on')); const e = $('m4c' + i); if (e) e.classList.add('on'); });
      document.querySelectorAll('#m4Out .on').forEach(e => e.classList.remove('on'));
      if (ok) { addStar(); $('m4Fb').innerHTML = '<b class="good">⭐ That\'s your name in Morse code! Try tapping it on the key.</b>'; }
    };
    $('m4Go').addEventListener('click', go); $('m4In').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); go(); } });
  } else if (m4.mode === 'guess') {
    const L = pick(EASY), opts = shuffle([L].concat(shuffle(EASY.filter(x => x !== L)).slice(0, 2))); m4.ans = L;
    b.innerHTML = `<button type="button" class="kz-btn" id="m4Hear">🔊 HEAR THE BEEPS</button><p class="dim">Which letter was that?</p><div class="kz-opts three">${opts.map(x => `<button type="button" class="kz-opt big" data-a="${x}">${x}<small>${dd(MC[x])}</small></button>`).join('')}</div><div class="kz-fb" id="m4Fb"></div>`;
    $('m4Hear').addEventListener('click', () => beepSeq(L));
    b.querySelectorAll('.kz-opt').forEach(x => x.addEventListener('click', () => {
      if (x.dataset.a === m4.ans) { x.classList.add('ok'); addStar(); $('m4Fb').innerHTML = `<b class="good">⭐ Yes! That was ${m4.ans}.</b>`; later(() => m4Draw(), 1300); }
      else { x.classList.add('no'); $('m4Fb').innerHTML = '<b class="bad">Listen again and try another!</b>'; }
    }));
    beepSeq(L);
  } else {
    const L = pick(EASY.concat(['K', 'R', 'D', 'U', 'W'])); m4.ans = L;
    b.innerHTML = `<div class="m4-target"><span>Tap this letter:</span><b>${L}</b><div>${dd(MC[L])}</div></div><button type="button" class="m4-key" id="m4Key" aria-label="Morse key">TAP<small>short tap = dot · hold = dash</small></button><div class="m4-got" id="m4Got"></div><div class="kz-fb" id="m4Fb"></div>`;
    const k = $('m4Key'), K = m4.key; K.code = '';
    const show = () => { $('m4Got').innerHTML = dd(K.code); };
    const finish = () => {
      const got = MD[K.code] || '?';
      if (got === m4.ans) { addStar(); $('m4Fb').innerHTML = `<b class="good">⭐ Perfect ${m4.ans}!</b>`; later(m4Draw, 1300); }
      else { $('m4Fb').innerHTML = `<b class="bad">That was ${got === '?' ? 'not a letter' : got}. Try again: ${m4.ans} is ${dd(MC[m4.ans])}</b>`; }
      K.code = ''; later(show, 900);
    };
    k.addEventListener('pointerdown', e => { e.preventDefault(); ac(); clearTimeout(K.timer); K.down = performance.now(); gn.gain.setTargetAtTime(0.5, AC.currentTime, 0.004); k.classList.add('down'); try { k.setPointerCapture(e.pointerId); } catch (x) {} });
    const up = e => { if (!K.down) return; e.preventDefault(); const d = performance.now() - K.down; K.down = 0; gn.gain.setTargetAtTime(0, AC.currentTime, 0.004); k.classList.remove('down'); K.code += d < 250 ? '.' : '-'; show(); const g = m4.g; K.timer = setTimeout(() => { if (g === m4.g) finish(); }, 900); };
    k.addEventListener('pointerup', up); k.addEventListener('pointercancel', up); k.addEventListener('contextmenu', e => e.preventDefault());
  }
}

function init() {
  if (!$('kzStars')) return;
  showStars();
  document.querySelectorAll('input[name=g1m]').forEach(r => r.addEventListener('change', () => { g1.mode = r.value; g1New(); }));
  $('g1Start').addEventListener('click', () => { $('g1Start').hidden = true; $('g1Play').hidden = false; g1New(); });
  $('g2Go').addEventListener('click', g2Go); $('g2In').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); g2Go(); } });
  $('g3Start').addEventListener('click', g3New); $('g3Again').addEventListener('click', g3Play); $('g3Ok').addEventListener('click', g3Check);
  $('g3In').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); g3Check(); } });
  document.querySelectorAll('input[name=g3l]').forEach(r => r.addEventListener('change', () => { g3.lvl = +r.value; }));
  $('kzChart').innerHTML = LETTERS.map(c => `<button type="button" class="kz-cell" data-c="${c}"><b>${c}</b><span>${NATO[c]}</span></button>`).join('');
  $('kzChart').querySelectorAll('.kz-cell').forEach(b => b.addEventListener('click', () => { hush(); say(NATO[b.dataset.c]); }));
  document.querySelectorAll('input[name=m4m]').forEach(r => r.addEventListener('change', () => { m4.mode = r.value; m4.g++; clearTimeout(m4.key.timer); m4.key.code = ''; mgen++; if (gn) gn.gain.setTargetAtTime(0, AC.currentTime, 0.01); m4Draw(); }));
  m4Draw();
  $('kzReset').addEventListener('click', () => { if (confirm('Start your stars over at zero?')) { stars = 0; try { localStorage.removeItem('kpcKidsStars'); } catch (e) {} showStars(); } });
}
window.KPCKIDS = { g1, g3, NATO, m4, MC };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
