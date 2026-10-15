/* KPC Kids Room: Radio Adventures — Ham Words Match, Map Hunt, Build-a-Radio, Fox Hunt, Weather Spotter.
   Stars go into the same kpcKidsStars count as the Kids Room. Nothing about the player is stored or sent. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1)), pick = a => a[Math.floor(Math.random() * a.length)];
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const NATO = { A: 'Alpha', B: 'Bravo', C: 'Charlie', D: 'Delta', E: 'Echo', F: 'Foxtrot', G: 'Golf', H: 'Hotel', I: 'India', J: 'Juliet', K: 'Kilo', L: 'Lima', M: 'Mike', N: 'November', O: 'Oscar', P: 'Papa', Q: 'Quebec', R: 'Romeo', S: 'Sierra', T: 'Tango', U: 'Uniform', V: 'Victor', W: 'Whiskey', X: 'X-ray', Y: 'Yankee', Z: 'Zulu', '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine' };
const phon = c => c.split('').map(ch => NATO[ch] || ch).join(' ');

/* stars (shared with the Kids Room) */
function stars() { try { return +localStorage.getItem('kpcKidsStars') || 0; } catch (e) { return 0; } }
function addStar(n) { const s = stars() + (n || 1); try { localStorage.setItem('kpcKidsStars', String(s)); } catch (e) {} const e = $('kgStars'); if (e) e.textContent = s; pop(`⭐ +${n || 1} star${(n || 1) > 1 ? 's' : ''}!`); }
let popT; function pop(t) { const p = $('kgPop'); if (!p) return; p.textContent = t; p.hidden = false; clearTimeout(popT); popT = setTimeout(() => { p.hidden = true; }, 2200); }

/* speech: the simple version that works on Android */
let VO = [], lastCancel = 0;
const loadV = () => { const v = (window.speechSynthesis && speechSynthesis.getVoices()) || []; VO = v.filter(x => /^en[-_]/i.test(x.lang)); if (/Android/i.test(navigator.userAgent)) { const l = VO.filter(x => x.localService); if (l.length) VO = l; } if (!VO.length) VO = v; };
if (window.speechSynthesis) { loadV(); speechSynthesis.onvoiceschanged = loadV; }
function hush() { if (window.speechSynthesis) { speechSynthesis.cancel(); lastCancel = Date.now(); } }
let SAYU = null;
function say(text, opt) {
  opt = opt || {};
  return new Promise(res => {
    if (!window.speechSynthesis) { res(); return; }
    setTimeout(() => {
      if (speechSynthesis.paused) speechSynthesis.resume();
      const u = new SpeechSynthesisUtterance(text); SAYU = u;
      if (VO.length) { const v = VO[(opt.vi || 0) % VO.length]; u.voice = v; u.lang = v.lang; } else u.lang = 'en-US';
      u.rate = opt.rate || 0.95; u.pitch = opt.pitch || 1;
      let done = false; const fin = () => { if (!done) { done = true; res(); } };
      setTimeout(fin, 1800 + text.length * 100 / u.rate); u.onend = u.onerror = fin; speechSynthesis.speak(u);
    }, Math.max(0, 150 - (Date.now() - lastCancel)));
  });
}
/* sound effects */
let AC = null;
function ac() { if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} } if (AC && AC.state === 'suspended') AC.resume(); return AC; }
function beep(freq, ms, vol) { const a = ac(); if (!a) return; const o = a.createOscillator(), g = a.createGain(), t = a.currentTime; o.frequency.value = freq; o.type = 'sine'; g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol == null ? 0.25 : vol, t + 0.01); g.gain.setTargetAtTime(0, t + ms / 1000, 0.01); o.connect(g); g.connect(a.destination); o.start(t); o.stop(t + ms / 1000 + 0.1); }
const yay = () => { beep(660, 90); setTimeout(() => beep(880, 90), 110); setTimeout(() => beep(1100, 140), 220); };
const oops = () => { beep(260, 160, 0.2); };

/* made-up call signs (4 letters after the number are never given out, so none is a real ham) */
const WORDS = ['FROG', 'BEAR', 'MOON', 'LAKE', 'TREE', 'FISH', 'ROCK', 'CAMP', 'OWLS', 'HAWK', 'DEER', 'PINE', 'STAR', 'MULE', 'FERN', 'DUCK', 'WOLF', 'BOAT', 'KITE', 'WAVE', 'NEST', 'BARN', 'COLT'];
const REGION = {}; ['1 CT ME MA NH RI VT', '2 NJ NY', '3 DE MD PA', '4 AL FL GA KY NC SC TN VA', '5 AR LA MS NM OK TX', '6 CA', '7 AZ ID MT NV OR UT WA WY', '8 MI OH WV', '9 IL IN WI', '0 CO IA KS MN MO NE ND SD'].forEach(r => { const p = r.split(' '); p.slice(1).forEach(k => { REGION[k] = p[0]; }); });
const fakeCall = st => pick(['K', 'W', 'N', 'KD', 'KC', 'AB']) + (REGION[st] || '4') + pick(WORDS);

/* =============== 1. HAM WORDS MATCH =============== */
const WORDLIST = [['CQ', 'Calling anyone who hears me'], ['QRZ', 'Who is calling me?'], ['QSL', 'I got it!'], ['QRT', 'I\'m turning my radio off'], ['QTH', 'Where I am (my location)'], ['73', 'Best wishes, goodbye'], ['Roger', 'I heard you'], ['Over', 'Your turn to talk'], ['Five nine', 'Loud and clear'], ['Again, again', 'Please say it one more time'], ['Net control', 'The ham who runs the net'], ['Rig', 'Your radio'], ['DX', 'A station far, far away'], ['Elmer', 'A ham who teaches new hams'], ['QRP', 'Using very low power'], ['Shack', 'The room where your radio lives']];
const WM = { first: null, lock: false, pairs: 0, moves: 0, n: 6 };
function wmNew() {
  WM.first = null; WM.lock = false; WM.pairs = 0; WM.moves = 0;
  const set = shuffle(WORDLIST).slice(0, WM.n);
  const cards = shuffle(set.flatMap((w, i) => [{ id: i, t: w[0], term: true }, { id: i, t: w[1], term: false }]));
  $('wmBoard').innerHTML = cards.map((c, k) => `<button type="button" class="wm-c${c.term ? ' term' : ''}" data-k="${k}" data-id="${c.id}" aria-label="Hidden card"><span class="b">📻</span><span class="f">${esc(c.t)}</span></button>`).join('');
  WM.set = set; $('wmMsg').textContent = 'Tap two cards. Find each ham word and what it means!';
}
function wmTap(btn) {
  if (WM.lock || btn.classList.contains('up') || btn.classList.contains('ok')) return;
  btn.classList.add('up'); btn.setAttribute('aria-label', btn.querySelector('.f').textContent); beep(520, 40, 0.12);
  if (!WM.first) { WM.first = btn; return; }
  const a = WM.first, b = btn; WM.first = null; WM.moves++;
  if (a.dataset.id === b.dataset.id && a.classList.contains('term') !== b.classList.contains('term')) {
    a.classList.add('ok'); b.classList.add('ok'); WM.pairs++; const w = WM.set[+a.dataset.id];
    $('wmMsg').textContent = `✅ ${w[0]} means "${w[1]}"`; hush(); say(`${w[0]}. ${w[1]}.`);
    if (WM.pairs === WM.n) { yay(); const st = WM.moves <= WM.n + 4 ? 3 : 2; addStar(st); $('wmMsg').textContent = `🎉 All matched in ${WM.moves} tries! ${st} stars. Tap NEW CARDS to play again.`; }
  } else {
    WM.lock = true; oops();
    setTimeout(() => { a.classList.remove('up'); b.classList.remove('up'); a.setAttribute('aria-label', 'Hidden card'); b.setAttribute('aria-label', 'Hidden card'); WM.lock = false; }, 1000);
  }
}

/* =============== 2. MAP HUNT =============== */
const MH = { states: null, ans: null, tries: 0, right: 0, mode: 'name' };
const SKIP = new Set(['AK', 'HI', 'PR', 'DC']);
const SMALL = ['VT', 'NH', 'MA', 'RI', 'CT', 'NJ', 'DE', 'MD'];
const KY = [-85.3, 37.5];
const proj = (lon, lat) => [(lon + 125) * 0.788 * 16, (50 - lat) * 16];
async function mhLoad() {
  if (MH.states) return;
  try { MH.states = (await (await fetch('kpc-us-states.json')).json()).filter(s => !SKIP.has(s.a)); } catch (e) { $('mhMsg').textContent = 'The map did not load. Refresh to try again.'; return; }
  const paths = MH.states.map(s => {
    const d = s.p.map(poly => poly.map(ring => 'M' + ring.map(([lo, la]) => proj(lo, la).map(v => v.toFixed(1)).join(',')).join('L') + 'Z').join('')).join('');
    let sx = 0, sy = 0, n = 0; s.p.forEach(poly => poly[0].forEach(([lo, la]) => { sx += lo; sy += la; n++; })); s.c = [sx / n, sy / n];
    return `<path d="${d}" data-st="${s.a}"><title>${esc(s.n)}</title></path>`;
  }).join('');
  const [kx, ky] = proj(KY[0], KY[1]);
  $('mhMap').innerHTML = `<svg viewBox="0 0 760 430" role="img" aria-label="Map of the United States">${paths}<circle cx="${kx.toFixed(1)}" cy="${ky.toFixed(1)}" r="5" class="mh-home"/></svg>`;
  $('mhSmall').innerHTML = SMALL.map(a => `<button type="button" class="mh-sb" data-st="${a}">${a}</button>`).join('');
}
function miles(a) { const s = MH.states.find(x => x.a === a); if (!s) return 0; const r = Math.PI / 180, x = (s.c[0] - KY[0]) * r * Math.cos((s.c[1] + KY[1]) / 2 * r), y = (s.c[1] - KY[1]) * r; return Math.round(Math.sqrt(x * x + y * y) * 3959); }
async function mhNew() {
  await mhLoad(); if (!MH.states) return;
  document.querySelectorAll('#mhMap path, .mh-sb').forEach(p => p.classList.remove('ok', 'no', 'hint'));
  const s = pick(MH.states.filter(x => x.a !== (MH.ans && MH.ans.a))); MH.ans = s; MH.tries = 0;
  const call = fakeCall(s.a);
  const hard = MH.mode === 'abbr';
  $('mhQ').innerHTML = `<b>📻 ${esc(call)}:</b> "You're five nine in <span class="mh-st">${esc(hard ? s.a : s.n)}</span>!"`;
  $('mhMsg').textContent = hard ? 'Only the two-letter abbreviation! Tap that state on the map.' : 'Where is that? Tap the state on the map.';
  hush(); say(`${phon(call)}. You're five nine in ${hard ? s.a.split('').join(' ') : s.n}.`);
}
function mhTap(a) {
  if (!MH.ans) return;
  const el = [...document.querySelectorAll(`[data-st="${a}"]`)];
  if (a === MH.ans.a) {
    el.forEach(e => e.classList.add('ok')); yay(); MH.right++;
    const d = miles(a), band = d < 120 ? 'That\'s home! On the radio you\'d hear Kentucky stations on 40 meters, or even on 2 meters nearby.' : d < 650 ? `That's about ${d} miles from Kentucky. Close by: you'd hear them best on 40 meters.` : `That's about ${d} miles from Kentucky. Far away: 20 meters skips that far!`;
    $('mhMsg').textContent = `✅ ${MH.ans.n} (${MH.ans.a})! ${band}`;
    if (MH.right % 5 === 0) addStar(1);
    $('mhScore').textContent = `${MH.right} found`;
    MH.ans = null; setTimeout(() => { if (!MH.ans) mhNew(); }, 3200);
  } else {
    el.forEach(e => { e.classList.add('no'); setTimeout(() => e.classList.remove('no'), 700); }); oops(); MH.tries++;
    const s = MH.states.find(x => x.a === a);
    $('mhMsg').textContent = `That's ${s ? s.n + ' (' + s.a + ')' : a}. Try again!${MH.tries >= 2 ? ' Look for the blinking state.' : ''}`;
    if (MH.tries >= 2) document.querySelectorAll(`[data-st="${MH.ans.a}"]`).forEach(e => e.classList.add('hint'));
  }
}

/* =============== 3. BUILD A RADIO =============== */
const PARTS = [
  { id: 'ant', icon: '📶', name: 'Antenna', slot: 'Up high in the tree', why: 'The antenna sends and catches radio waves. Higher is better!' },
  { id: 'coax', icon: '〰️', name: 'Coax cable', slot: 'From the antenna down to the radio', why: 'Coax is a special wire that carries the signal between the antenna and the radio.' },
  { id: 'rig', icon: '📻', name: 'Radio', slot: 'On the table', why: 'The radio (hams call it a rig) turns your voice into radio waves, and radio waves back into sound.' },
  { id: 'bat', icon: '🔋', name: 'Battery', slot: 'Power for the radio', why: 'Every radio needs power. In the park, hams use a battery. At home, a power supply.' },
  { id: 'mic', icon: '🎤', name: 'Microphone', slot: 'Something to talk into', why: 'You talk into the microphone. Press the button to talk, let go to listen!' }
];
const SILLY = [{ id: 'x1', icon: '🍌', name: 'Banana', no: 'A banana can\'t send radio waves. But it makes a good snack while you\'re on the air!' }, { id: 'x2', icon: '🧦', name: 'Sock', no: 'A sock?! Keep that on your foot.' }, { id: 'x3', icon: '🪥', name: 'Toothbrush', no: 'Nice and clean, but a toothbrush isn\'t a radio part!' }, { id: 'x4', icon: '🥫', name: 'Soup can', no: 'Tin can phones need a string, not a radio. Try again!' }];
const BR = { sel: null, done: new Set() };
function brNew() {
  BR.sel = null; BR.done = new Set();
  $('brTray').innerHTML = shuffle(PARTS.concat(shuffle(SILLY).slice(0, 3))).map(p => `<button type="button" class="br-p" data-p="${p.id}"><span>${p.icon}</span>${esc(p.name)}</button>`).join('');
  $('brScene').innerHTML = PARTS.map(p => `<button type="button" class="br-s br-${p.id}" data-s="${p.id}"><b>?</b><small>${esc(p.slot)}</small></button>`).join('') + '<div class="br-tree">🌳</div><div class="br-table"></div><div class="br-lamp" id="brLamp"></div>';
  $('brMsg').textContent = 'Tap a part, then tap where it goes.';
  $('brScene').classList.remove('on');
}
function brPick(id) {
  const silly = SILLY.find(x => x.id === id);
  document.querySelectorAll('.br-p').forEach(b => b.classList.toggle('sel', b.dataset.p === id));
  BR.sel = id;
  if (silly) { oops(); $('brMsg').textContent = `${silly.icon} ${silly.no}`; BR.sel = null; const b = document.querySelector(`[data-p="${id}"]`); if (b) b.classList.add('gone'); }
  else $('brMsg').textContent = 'Now tap where it goes.';
}
function brPlace(slot) {
  if (!BR.sel || BR.done.has(slot)) return;
  const p = PARTS.find(x => x.id === BR.sel);
  if (BR.sel !== slot) { oops(); $('brMsg').textContent = `Hmm, the ${p.name.toLowerCase()} doesn't go there. Read the hints!`; return; }
  BR.done.add(slot); beep(700, 80);
  const s = document.querySelector(`[data-s="${slot}"]`); s.classList.add('ok'); s.innerHTML = `<span>${p.icon}</span><small>${esc(p.name)}</small>`;
  const b = document.querySelector(`[data-p="${slot}"]`); if (b) b.classList.add('gone');
  BR.sel = null; $('brMsg').textContent = `✅ ${p.why}`;
  if (BR.done.size === PARTS.length) {
    $('brScene').classList.add('on'); yay(); addStar(2);
    $('brMsg').textContent = '🎉 Your station is on the air! Listen: you\'re calling CQ!';
    say('C Q, C Q, C Q. This is Whiskey Four Kilo India Delta Sierra, calling C Q!', { rate: 1 });
  }
}

/* =============== 4. FOX HUNT =============== */
const FX = { n: 9, me: [4, 8], fox: [0, 0], steps: 0, dir: 0, on: false, found: 0, mode: 'easy', t: null };
const SCENE = ['🌳', '🌲', '🪨', '🌼', '🌿', '🍄'];
function fxNew() {
  const n = FX.n; FX.me = [Math.floor(n / 2), n - 1]; FX.steps = 0; FX.dir = 0; FX.on = true;
  do { FX.fox = [rnd(0, n - 1), rnd(0, n - 3)]; } while (Math.abs(FX.fox[0] - FX.me[0]) + Math.abs(FX.fox[1] - FX.me[1]) < 5);
  FX.deco = Array.from({ length: n * n }, () => Math.random() < 0.18 ? pick(SCENE) : '');
  fxDraw(); $('fxMsg').textContent = FX.mode === 'easy' ? 'Walk around. The beeps get LOUDER and FASTER when you get close to the fox!' : 'Turn your antenna 🔄 and watch the meter. It\'s strongest when the antenna points at the fox. Then walk that way!';
  fxLoop();
}
function fxSig() {
  const dx = FX.fox[0] - FX.me[0], dy = FX.fox[1] - FX.me[1], d = Math.sqrt(dx * dx + dy * dy);
  let s = Math.max(0, 1 - d / 10);
  if (FX.mode === 'pro' && d > 0) { const a = Math.atan2(dy, dx), f = [-Math.PI / 2, 0, Math.PI / 2, Math.PI][FX.dir]; s *= 0.25 + 0.75 * Math.max(0, Math.cos(a - f)); }
  return d === 0 ? 1 : s;
}
function fxDraw() {
  const n = FX.n;
  let h = '';
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const me = FX.me[0] === x && FX.me[1] === y, adj = Math.abs(FX.me[0] - x) + Math.abs(FX.me[1] - y) === 1;
    h += `<button type="button" class="fx-c${adj ? ' adj' : ''}" data-x="${x}" data-y="${y}" ${adj ? '' : 'tabindex="-1"'} aria-label="${me ? 'You' : adj ? 'Walk here' : ''}">${me ? `<span class="fx-me">${!FX.on && FX.fox[0] === x && FX.fox[1] === y ? '🦊' : '🧒'}<i class="fx-ant d${FX.dir}">📡</i></span>` : (FX.on ? FX.deco[y * n + x] : (FX.fox[0] === x && FX.fox[1] === y ? '🦊' : FX.deco[y * n + x]))}</button>`;
  }
  $('fxGrid').innerHTML = h;
  const s = fxSig(); $('fxMeter').style.width = Math.round(s * 100) + '%'; $('fxSteps').textContent = FX.steps + ' steps';
}
function fxMove(dx, dy) {
  if (!FX.on) return;
  const x = FX.me[0] + dx, y = FX.me[1] + dy; if (x < 0 || y < 0 || x >= FX.n || y >= FX.n) return;
  FX.me = [x, y]; FX.steps++; if (FX.mode === 'easy') FX.dir = dy < 0 ? 0 : dx > 0 ? 1 : dy > 0 ? 2 : 3;
  if (x === FX.fox[0] && y === FX.fox[1]) {
    FX.on = false; clearTimeout(FX.t); fxDraw(); yay(); FX.found++;
    const par = Math.abs(FX.fox[0] - 4) + Math.abs(FX.fox[1] - 8) + 4, st = FX.steps <= par ? 2 : 1; addStar(st);
    $('fxMsg').textContent = `🦊 You found the fox in ${FX.steps} steps! ${st} star${st > 1 ? 's' : ''}. Real hams hide a little transmitter (the "fox") and hunt it with antennas. Tap NEW FOX to play again.`;
    return;
  }
  fxDraw();
}
function fxTurn() { FX.dir = (FX.dir + 1) % 4; fxDraw(); }
function fxLoop() {
  clearTimeout(FX.t); if (!FX.on || !$('fxGrid') || document.hidden) return;
  const s = fxSig();
  if (!FX.mute) beep(500 + s * 700, 70, 0.04 + s * 0.3);
  FX.t = setTimeout(fxLoop, 1100 - s * 850);
}

/* =============== 5. WEATHER SPOTTER =============== */
const WX = [
  { pic: '🌥️', see: 'Big dark clouds are rolling in, but nothing is happening yet.', nc: 'This is the SKYWARN weather net. Spotters with severe weather to report, please call now.', a: [['Listen and stay ready. Nothing to report yet.', 1, 'Right! Only call in when you see something to report. Keeping the radio quiet lets the real reports through.'], ['Call in: "It\'s cloudy here!"', 0, 'Clouds alone aren\'t a report. Net control is waiting for severe weather, so keep the frequency clear.'], ['Talk about your new bike', 0, 'Not during a weather net! Save the fun chat for later.']] },
  { pic: '🧊', see: 'Ice is falling from the sky! The hailstones look about as big as a quarter.', nc: 'Spotters, any hail reports?', a: [['"W4KIDS, quarter-size hail in Cave City."', 1, 'Perfect! Say who you are, what you see, how big (compare to a coin), and where.'], ['"BIG HAIL!!!"', 0, 'Too vague. How big? Where? Compare it to a coin or ball: pea, penny, quarter, golf ball.'], ['Run outside to measure the hail', 0, 'Never go out in hail! Look from a safe window. Hail can hurt.']] },
  { pic: '🌳', see: 'The wind blew a big tree branch down across your road.', nc: 'Net control here. Any damage reports?', a: [['"W4KIDS, a large tree limb is blocking Main Street."', 1, 'Great report! Damage that blocks a road helps the road crew and the weather service.'], ['Go climb on the branch', 0, 'Stay away from fallen trees. There might be power lines tangled in them!'], ['Say nothing, it\'s just a branch', 0, 'A branch blocking the road IS worth reporting when net control asks for damage.']] },
  { pic: '🌪️', see: 'You see a dark cloud spinning and a funnel coming down!', nc: 'All stations, stand by…', a: [['Go to the basement or a small inside room right away', 1, 'YES! Safety first, always. A grown-up calls 911. Reports come after everyone is safe.'], ['Go outside to take a video', 0, 'No! Get to shelter right away. Nothing is more important than being safe.'], ['Wait for your turn on the net', 0, 'Not now! When you see a tornado, take shelter first. Let a grown-up call 911.']] },
  { pic: '🎙️', see: 'Net control is talking with another spotter. You have a report, but it\'s not an emergency.', nc: '…go ahead with your report, KD4HAWK.', a: [['Wait until net control asks for more reports', 1, 'Right! Good hams wait their turn. Talking over someone means nobody hears either of you.'], ['Talk right over them', 0, 'That\'s called doubling. Both signals get garbled and nobody can understand.'], ['Turn the radio off', 0, 'Stay on and listen! You\'ll get your turn soon.']] },
  { pic: '🌊', see: 'Water from the creek is running over the road, and you can\'t see the road under it.', nc: 'Any flooding reports?', a: [['"W4KIDS, water over Highway 31 by the creek."', 1, 'Excellent! Flooded roads are dangerous. Remember: Turn Around, Don\'t Drown!'], ['It\'s fine to drive through slowly', 0, 'Never! Just a little moving water can wash a car away. Turn around, don\'t drown.'], ['Go splash in it', 0, 'Flood water is dangerous and dirty. Stay far away!']] },
  { pic: '🌤️', see: 'The storm has passed and the sun is peeking out.', nc: 'Thanks to all spotters. This net is now closed. Seventy-three.', a: [['Keep listening in case more storms come', 1, 'Smart! Storms can come in waves. Good spotters stay ready.'], ['Shout "WOO!" on the radio', 0, 'The net is closed, but keep it polite. Just listen!'], ['Throw your radio in the closet', 0, 'Keep it ready! Next time you might help someone.']] }
];
const WS = { i: 0, score: 0 };
function wsShow() {
  const sc = WX[WS.i];
  if (!sc) { const st = WS.score >= 6 ? 3 : WS.score >= 4 ? 2 : 1; addStar(st); $('wsBox').innerHTML = `<div class="ws-pic">🏅</div><h3>Weather Spotter: ${WS.score} of ${WX.length} right!</h3><p>Real weather spotters take a free SKYWARN class from the National Weather Service. Hams and their radios help warn people when storms come. Ask a grown-up if there's a class near you!</p><button type="button" class="kz-btn" id="wsAgain">▶ PLAY AGAIN</button>`; $('wsAgain').addEventListener('click', () => { WS.i = 0; WS.score = 0; wsShow(); }); return; }
  $('wsBox').innerHTML = `<div class="ws-step">Scene ${WS.i + 1} of ${WX.length}</div><div class="ws-pic">${sc.pic}</div><p class="ws-see">${esc(sc.see)}</p><p class="ws-nc">📻 <b>Net control:</b> "${esc(sc.nc)}"</p><p class="ws-q">What do you do?</p><div class="ws-a">${shuffle(sc.a).map(a => `<button type="button" class="ws-b" data-ok="${a[1]}" data-why="${esc(a[2])}">${esc(a[0])}</button>`).join('')}</div><p class="ws-fb" id="wsFb"></p>`;
  hush(); say(sc.nc, { vi: 1, rate: 0.95, pitch: 0.85 });
}
function wsPick(b) {
  if ($('wsBox').querySelector('.ws-b.ok, .ws-b.no.final')) return;
  const ok = b.dataset.ok === '1';
  b.classList.add(ok ? 'ok' : 'no');
  $('wsFb').textContent = (ok ? '✅ ' : '❌ ') + b.dataset.why;
  if (ok) { yay(); if (!WS.miss) WS.score++; WS.miss = false; setTimeout(() => { WS.i++; wsShow(); }, 3200); }
  else { oops(); WS.miss = true; }
}

/* =============== wiring =============== */
function init() {
  if (!$('kgStars')) return;
  $('kgStars').textContent = stars();
  /* words */
  $('wmBoard').addEventListener('click', e => { const c = e.target.closest('.wm-c'); if (c) wmTap(c); });
  $('wmNew').addEventListener('click', wmNew); wmNew();
  /* map */
  document.querySelectorAll('input[name=mhm]').forEach(r => r.addEventListener('change', () => { MH.mode = r.value; mhNew(); }));
  $('mhGo').addEventListener('click', () => { ac(); mhNew(); });
  $('mhAgain').addEventListener('click', () => { if (!MH.ans) return; hush(); say(`You're five nine in ${MH.mode === 'abbr' ? MH.ans.a.split('').join(' ') : MH.ans.n}.`); });
  $('mhMap').addEventListener('click', e => { const p = e.target.closest('[data-st]'); if (p) mhTap(p.dataset.st); });
  $('mhSmall').addEventListener('click', e => { const p = e.target.closest('[data-st]'); if (p) mhTap(p.dataset.st); });
  mhLoad();
  /* build */
  $('brTray').addEventListener('click', e => { const b = e.target.closest('.br-p'); if (b && !b.classList.contains('gone')) brPick(b.dataset.p); });
  $('brScene').addEventListener('click', e => { const s = e.target.closest('.br-s'); if (s) brPlace(s.dataset.s); });
  $('brNew').addEventListener('click', brNew); brNew();
  /* fox */
  $('fxGrid').addEventListener('click', e => { const c = e.target.closest('.fx-c.adj'); if (c) { ac(); fxMove(+c.dataset.x - FX.me[0], +c.dataset.y - FX.me[1]); } });
  [['fxU', 0, -1], ['fxD', 0, 1], ['fxL', -1, 0], ['fxR', 1, 0]].forEach(([id, dx, dy]) => $(id).addEventListener('click', () => { ac(); fxMove(dx, dy); }));
  $('fxTurn').addEventListener('click', () => { ac(); fxTurn(); });
  $('fxNew').addEventListener('click', () => { ac(); fxNew(); });
  $('fxMute').addEventListener('click', () => { FX.mute = !FX.mute; $('fxMute').textContent = FX.mute ? '🔇 SOUND OFF' : '🔊 SOUND ON'; });
  document.querySelectorAll('input[name=fxm]').forEach(r => r.addEventListener('change', () => { FX.mode = r.value; $('fxTurn').style.visibility = FX.mode === 'pro' ? 'visible' : 'hidden'; fxNew(); }));
  document.addEventListener('keydown', e => {
    const box = $('fxBox'); if (!box || !FX.on) return; const r = box.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return;
    const m = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0] }[e.key]; if (m && !/INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) { e.preventDefault(); ac(); fxMove(m[0], m[1]); }
  });
  FX.on = false; FX.deco = Array.from({ length: 81 }, () => Math.random() < 0.18 ? pick(SCENE) : ''); FX.fox = [-1, -1]; fxDraw(); $('fxMsg').textContent = 'Press ▶ START HUNT. A fox is hiding somewhere in the park!';
  $('fxStart').addEventListener('click', () => { ac(); $('fxStart').hidden = true; fxNew(); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden && FX.on) fxLoop(); });
  /* weather */
  $('wsBox').addEventListener('click', e => { const b = e.target.closest('.ws-b'); if (b) wsPick(b); });
  $('wsStart').addEventListener('click', () => { $('wsStart').hidden = true; WS.i = 0; WS.score = 0; wsShow(); });
}
window.KPCKG = { MH, BR, FX, WS, mhTap, brPick, brPlace, fxMove };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
