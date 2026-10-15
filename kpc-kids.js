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
  $('kzReset').addEventListener('click', () => { if (confirm('Start your stars over at zero?')) { stars = 0; try { localStorage.removeItem('kpcKidsStars'); } catch (e) {} showStars(); } });
}
window.KPCKIDS = { g1, g3, NATO };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
