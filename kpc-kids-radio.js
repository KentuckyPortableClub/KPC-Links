/* KPC Kids Room: Spin the Dial — a pretend ham radio receiver.
   Turn it on, pick a band, spin the knob (or SCAN) and listen: voice contacts in the talking zone
   (browser speech voices, one at a time) and Morse code in the CW zone (Web Audio beeps, with the
   letters shown as they're sent). All call signs are made up with 4 letters after the number,
   which the FCC never issues, so none can belong to a real ham. Nothing is sent anywhere. */
(() => {
'use strict';
const $ = id => document.getElementById(id);
const pick = a => a[Math.floor(Math.random() * a.length)];
const rnd = (a, b) => a + Math.floor(Math.random() * (b - a + 1));
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };
const store = { get(k, d) { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };

const NATO = { A: 'Alpha', B: 'Bravo', C: 'Charlie', D: 'Delta', E: 'Echo', F: 'Foxtrot', G: 'Golf', H: 'Hotel', I: 'India', J: 'Juliet', K: 'Kilo', L: 'Lima', M: 'Mike', N: 'November', O: 'Oscar', P: 'Papa', Q: 'Quebec', R: 'Romeo', S: 'Sierra', T: 'Tango', U: 'Uniform', V: 'Victor', W: 'Whiskey', X: 'X-ray', Y: 'Yankee', Z: 'Zulu', '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '/': 'portable' };
const DIG = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine'];
const phon = c => c.split('').map(ch => NATO[ch] || ch).join(' ');
const sayRef = r => String(r).replace(/[A-Z]/g, c => c + ' ').replace(/\d/g, d => ' ' + DIG[+d] + ' ').replace(/[-/]/g, ' ').replace(/\s+/g, ' ').trim();

/* made-up calls: 4 letters after the number = never issued in the US */
const WORDS = ['FROG', 'BEAR', 'MOON', 'LAKE', 'TREE', 'FISH', 'ROCK', 'CAMP', 'OWLS', 'HAWK', 'DEER', 'PINE', 'CAVE', 'LAMP', 'RAIN', 'SNOW', 'STAR', 'MULE', 'FERN', 'HILL', 'CORN', 'DUCK', 'WOLF', 'BOAT', 'KITE', 'FIRE', 'SAND', 'BELL', 'COAL', 'HORN', 'MOSS', 'PEAK', 'WAVE', 'NEST', 'BARN', 'COLT'];
const PFX = ['K', 'W', 'N', 'KD', 'KC', 'KB', 'KE', 'AB', 'AC', 'KJ', 'KI', 'WB'];
let usedCalls = new Set();
function fakeCall(region) {
  for (let i = 0; i < 200; i++) { const c = pick(PFX) + (region != null ? region : pick([4, 4, 4, 8, 9, 5, 3, 0, 1, 2, 6, 7])) + pick(WORDS); if (!usedCalls.has(c)) { usedCalls.add(c); return c; } }
  return 'K4' + pick(WORDS);
}
const STATES = [['Kentucky', 4], ['Tennessee', 4], ['Ohio', 8], ['Indiana', 9], ['West Virginia', 8], ['Virginia', 4], ['Texas', 5], ['Florida', 4], ['Michigan', 8], ['Illinois', 9], ['Georgia', 4], ['Colorado', 0], ['California', 6], ['New York', 2], ['Maine', 1], ['Missouri', 0], ['Alabama', 4], ['Oregon', 7]];
const STAB = { Kentucky: 'KY', Tennessee: 'TN', Ohio: 'OH', Indiana: 'IN', 'West Virginia': 'WV', Virginia: 'VA', Texas: 'TX', Florida: 'FL', Michigan: 'MI', Illinois: 'IL', Georgia: 'GA', Colorado: 'CO', California: 'CA', 'New York': 'NY', Maine: 'ME', Missouri: 'MO', Alabama: 'AL', Oregon: 'OR' };
const MEN = ['Bob', 'Earl', 'Jim', 'Ray', 'Hank', 'Tom', 'Gus', 'Walt', 'Dale', 'Frank', 'Roy', 'Larry'];
const WOMEN = ['Sue', 'Linda', 'Carol', 'Dottie', 'Maggie', 'Ruth', 'Jan', 'Peggy', 'Barb', 'Donna'];
const KIDS = [['Emma', 0], ['Jake', 1], ['Lily', 0], ['Noah', 1], ['Ava', 0], ['Eli', 1], ['Mia', 0], ['Owen', 1]];
let TOWNS = ['Bowling Green', 'Frankfort', 'Hazard', 'Paducah', 'Somerset', 'Bardstown', 'London', 'Cave City', 'Murray', 'Ashland', 'Elizabethtown', 'Pikeville'];
let PARKS = [{ c: 'US-1271', n: 'a state park' }], SUMMITS = [{ c: 'W4K/EC-001', n: 'Black Mountain' }], KFFS = [{ c: 'KFF-0019', n: 'Cumberland Gap' }];
fetch('kpc-ky-data.json').then(r => r.json()).then(d => {
  const ok = s => s && s.c && s.n && s.n.length < 46;
  if (d.parks) { const p = d.parks.filter(ok); if (p.length) PARKS = p; }
  if (d.summits) { const p = d.summits.filter(ok); if (p.length) SUMMITS = p; }
  if (d.kff) { const p = d.kff.filter(ok); if (p.length) KFFS = p; }
  if (d.towns && d.towns.length) TOWNS = d.towns.map(t => t.n).filter(Boolean);
  if (on) buildBand(true);
}).catch(() => {});

/* ---------------- people ---------------- */
let vi = 0;
function person(o) {
  o = o || {};
  const kid = o.kid ? pick(KIDS) : null;
  const m = kid ? !!kid[1] : (o.m != null ? o.m : Math.random() < 0.65);
  const st = o.st || pick(STATES);
  return {
    call: o.call || fakeCall(o.ky ? 4 : st[1]), name: kid ? kid[0] : pick(m ? MEN : WOMEN), m, kid: !!kid, age: kid ? rnd(9, 13) : 0,
    st: st[0], town: o.ky || st[0] === 'Kentucky' ? pick(TOWNS) : '',
    pitch: kid ? 1.45 + Math.random() * 0.25 : m ? 0.55 + Math.random() * 0.3 : 1 + Math.random() * 0.25,
    rate: kid ? 1.05 : 0.92 + Math.random() * 0.15, vi: vi++, s: 0.55 + Math.random() * 0.45
  };
}
const KY = ['Kentucky', 4];

/* ---------------- what each kind of station is ---------------- */
const KINDS = {
  pota: { icon: '🌲', name: 'POTA activator', zone: 'talk', why: 'Someone set up a radio in a <b>park</b> and is calling "CQ POTA". Hams at home (hunters) call back to collect the park. The activator needs 10 contacts!' },
  p2p: { icon: '🤝', name: 'Park to Park', zone: 'talk', why: 'Two hams, each sitting in a <b>different park</b>, are talking to each other. That\'s called <b>park to park</b>, and they both get credit for two parks.' },
  kff: { icon: '🦉', name: 'KFF (flora & fauna)', zone: 'talk', why: 'KFF is World Wide Flora and Fauna: hams go on the air from places that protect <b>plants and animals</b>, like forests and wildlife areas. They need 44 contacts for full credit!' },
  sota: { icon: '⛰️', name: 'SOTA summit', zone: 'talk', why: 'Summits on the Air: this ham <b>hiked up a mountain</b> carrying a small radio and is calling from the top. Only 4 contacts count, but the hike is the hard part!' },
  rag: { icon: '☕', name: 'Ragchew', zone: 'talk', why: 'A <b>ragchew</b> is just friends chatting on the radio: the weather, their radios, what they ate for supper. Some hams talk every week for years.' },
  net: { icon: '📋', name: 'Net (radio meeting)', zone: 'talk', why: 'A <b>net</b> is a meeting on the air. One ham is <b>net control</b> and runs it, and others "check in" one at a time so nobody talks over each other. Nets help a lot in storms and emergencies.' },
  kid: { icon: '🧒', name: 'Young ham', zone: 'talk', why: 'That\'s a <b>kid</b> on the air! There is no age limit for a ham radio license. Some hams pass the test when they\'re 8 or 9 years old.' },
  cwcq: { icon: '📣', name: 'Morse CQ', zone: 'cw', why: 'Beep beep! This ham is calling <b>CQ</b> in Morse code. CQ means "calling anyone". DE means "from", and K means "your turn".' },
  cwpota: { icon: '🌳', name: 'Morse POTA', zone: 'cw', why: 'A park activator using <b>Morse code</b> instead of a microphone. Morse gets through even when signals are really weak, so lots of park hams use it. 5NN means "you\'re five nine".' },
  cwrag: { icon: '🗨️', name: 'Morse ragchew', zone: 'cw', why: 'Two friends chatting in <b>Morse code</b>! They use short words: WX = weather, RIG = radio, ANT = antenna, ES = and, FB = fine business (great!).' },
  cwsota: { icon: '🏔️', name: 'Morse summit to summit', zone: 'cw', why: 'Two hams on <b>two different mountains</b> talking in Morse code. S2S means summit to summit. /P means portable.' },
  cwslow: { icon: '🐢', name: 'Slow Morse', zone: 'cw', why: 'This ham is sending <b>slow</b> Morse code, so new hams can copy it. When you ask someone to slow down you send QRS. Everybody starts slow!' }
};
const KIND_ORDER = ['pota', 'p2p', 'kff', 'sota', 'rag', 'net', 'kid', 'cwcq', 'cwpota', 'cwrag', 'cwsota', 'cwslow'];

/* ham words to explain when they show up */
const GLOSS = [
  [/\bCQ\b/i, 'CQ', 'calling anyone who hears me'], [/\bQRZ\b/i, 'QRZ', 'who is calling me?'], [/\bQSL\b/i, 'QSL', 'I got it'], [/\b(73|seventy-three)\b/i, '73', 'best wishes, goodbye'],
  [/\b(five nine|5NN|599)\b/i, '5-9', 'your signal is loud and clear'], [/\broger\b|\bR R\b/i, 'Roger', 'I heard you'], [/\bpark to park\b|\bP2P\b/i, 'Park to park', 'both hams are in parks'],
  [/\bDE\b/, 'DE', 'from'], [/\bTU\b/, 'TU', 'thank you'], [/\bKN\b/, 'KN', 'only you go ahead'], [/ K$|\bK\b(?=\s|$)/, 'K', 'over, your turn'], [/\bFB\b/, 'FB', 'fine business = great!'],
  [/\bWX\b/, 'WX', 'weather'], [/\bHR\b/, 'HR', 'here'], [/\bES\b/, 'ES', 'and'], [/\bUR\b/, 'UR', 'your'], [/\bRIG\b/, 'RIG', 'radio'], [/\bANT\b/, 'ANT', 'antenna'], [/<BT>|=/, 'BT', 'pause, new thought'],
  [/<SK>/, 'SK', 'end of contact'], [/\bS2S\b|summit to summit/i, 'S2S', 'summit to summit'], [/\/P\b|portable/i, '/P', 'portable (not at home)'], [/\bGM\b/, 'GM', 'good morning'], [/\bNAME\b/, 'NAME', 'my name is'],
  [/\bQRS\b/, 'QRS', 'please send slower'], [/\bover\b/i, 'Over', 'your turn to talk'], [/\bclear\b/i, 'Clear', 'I\'m done, leaving the radio'], [/net control/i, 'Net control', 'the ham who runs the net'],
  [/check-?ins?/i, 'Check in', 'say your call to join the net'], [/again,? again/i, 'Again again', 'please say that one more time'], [/\bPOTA\b|Parks on the Air/i, 'POTA', 'Parks on the Air'],
  [/\bSOTA\b|Summits on the Air/i, 'SOTA', 'Summits on the Air'], [/\bKFF\b|K F F|W W F F/i, 'KFF', 'flora and fauna program'], [/\bGL\b/, 'GL', 'good luck'], [/\bCUL\b/, 'CUL', 'see you later'], [/\bEE\b/, 'EE', 'a friendly "dit dit" goodbye']
];

/* ---------------- scripts ----------------
   Voice lines: [speaker, spoken words, words shown on screen]. Calls are spoken in phonetics. */
function voiceScript(kind) {
  const L = [];
  const say = (i, spoken, shown) => L.push([i, spoken, shown || spoken]);
  let sp;
  if (kind === 'pota' || kind === 'kff') {
    const a = person({ st: KY, ky: 1 }), hs = [person(), person(), person()], ref = kind === 'kff' ? pick(KFFS) : pick(PARKS);
    sp = [a].concat(hs);
    const cq = kind === 'kff' ? 'CQ W W F F, CQ K F F' : 'CQ Parks on the Air, CQ POTA', cqS = kind === 'kff' ? 'CQ WWFF, CQ KFF' : 'CQ Parks on the Air, CQ POTA';
    say(0, `${cq}, this is ${phon(a.call)}, ${phon(a.call)}, portable at ${ref.n}, ${sayRef(ref.c)}.`, `${cqS}, this is ${a.call}, ${a.call}, portable at ${ref.n}, ${ref.c}.`);
    say(1, phon(hs[0].call), hs[0].call);
    say(0, `${phon(hs[0].call)}, thanks for the call. You're five nine in Kentucky. Five nine.`, `${hs[0].call}, thanks for the call. You're five nine in Kentucky. Five nine.`);
    say(1, `Roger roger! You're five nine also, in ${hs[0].st}. Thanks for the ${kind === 'kff' ? 'reference' : 'park'}. Seventy-three!`);
    say(0, `Thank you, seventy-three. QRZ? This is ${phon(a.call)}.`, `Thank you, 73. QRZ? This is ${a.call}.`);
    say(2, phon(hs[1].call.slice(-2)), hs[1].call.slice(-2) + ' (just the end of the call)');
    say(0, `Station ending in ${phon(hs[1].call.slice(-2))}, again, again?`, `Station ending in ${hs[1].call.slice(-2)}, again, again?`);
    say(2, `${phon(hs[1].call)}, ${phon(hs[1].call)}.`, `${hs[1].call}, ${hs[1].call}.`);
    say(0, `${phon(hs[1].call)}, you're five seven, five seven, Kentucky.`, `${hs[1].call}, you're five seven, five seven, Kentucky.`);
    say(2, `QSL. You're five nine in ${hs[1].st}. Have fun out there, seventy-three.`);
    say(0, `Seventy-three. QRZ for ${phon(a.call)}, ${kind === 'kff' ? 'K F F' : 'POTA'}.`, `73. QRZ for ${a.call}, ${kind === 'kff' ? 'KFF' : 'POTA'}.`);
    say(3, phon(hs[2].call), hs[2].call);
    say(0, `${phon(hs[2].call)}, you're five nine Kentucky.`, `${hs[2].call}, you're five nine Kentucky.`);
    say(3, `Thanks! Five eight ${hs[2].st}. Seventy-three.`);
    return { sp, lines: L, about: `${a.call} (${a.name}) is at ${ref.n}, ${ref.c}. Hunters are calling from ${hs.map(h => h.st).join(', ')}.` };
  }
  if (kind === 'p2p') {
    const a = person({ st: KY, ky: 1 }), b = person(), pa = pick(PARKS), pb = { c: 'US-' + String(rnd(1, 9999)).padStart(4, '0'), n: 'a park in ' + b.st };
    sp = [a, b];
    say(0, `CQ POTA, CQ POTA, this is ${phon(a.call)} at ${pa.n}.`, `CQ POTA, CQ POTA, this is ${a.call} at ${pa.n}.`);
    say(1, `Park to park! ${phon(b.call)}, ${phon(b.call)}.`, `Park to park! ${b.call}, ${b.call}.`);
    say(0, `Park to park, go ahead ${phon(b.call)}!`, `Park to park, go ahead ${b.call}!`);
    say(1, `You're five nine, five nine. I'm in ${pb.n}, ${sayRef(pb.c)}. ${sayRef(pb.c)}.`, `You're five nine, five nine. I'm in ${pb.n}, ${pb.c}. ${pb.c}.`);
    say(0, `Roger, ${sayRef(pb.c)}. You're five eight. I'm at ${sayRef(pa.c)}, in Kentucky. Thanks for the park to park!`, `Roger, ${pb.c}. You're five eight. I'm at ${pa.c}, in Kentucky. Thanks for the park to park!`);
    say(1, `QSL! Great contact, two parks each. Seventy-three!`);
    say(0, `Seventy-three. QRZ for ${phon(a.call)}, POTA.`, `73. QRZ for ${a.call}, POTA.`);
    return { sp, lines: L, about: `${a.call} is at ${pa.n} (${pa.c}). ${b.call} (${b.name}) is in ${pb.n} (${pb.c}).` };
  }
  if (kind === 'sota') {
    const a = person({ st: KY, ky: 1 }), h = [person(), person()], s = pick(SUMMITS);
    sp = [a].concat(h);
    say(0, `CQ SOTA, CQ Summits on the Air. This is ${phon(a.call)} portable, on ${s.n}, ${sayRef(s.c)}. It's windy up here!`, `CQ SOTA, CQ Summits on the Air. This is ${a.call}/P on ${s.n}, ${s.c}. It's windy up here!`);
    say(1, phon(h[0].call), h[0].call);
    say(0, `${phon(h[0].call)}, you're five five. I'm running five watts from the summit, my battery fits in my pocket.`, `${h[0].call}, you're five five. I'm running five watts from the summit, my battery fits in my pocket.`);
    say(1, `Roger, you're a strong five nine into ${h[0].st}. Great signal from the mountain! Seventy-three.`);
    say(0, `Seventy-three. I need two more to activate. QRZ?`, `73. I need two more to activate. QRZ?`);
    say(2, phon(h[1].call), h[1].call);
    say(0, `${phon(h[1].call)}, five seven, five seven.`, `${h[1].call}, five seven, five seven.`);
    say(2, `QSL, five nine ${h[1].st}. Be careful hiking down! Seventy-three.`);
    return { sp, lines: L, about: `${a.call} (${a.name}) hiked up ${s.n}, ${s.c}${s.ft ? ', ' + s.ft + ' feet high' : ''}.` };
  }
  if (kind === 'rag') {
    const a = person({ st: KY, ky: 1, m: true }), b = person({ st: KY, ky: 1 });
    sp = [a, b];
    say(0, `${phon(b.call)}, this is ${phon(a.call)}. Good to hear you again, ${b.name}. How's the weather down your way? Over.`, `${b.call}, this is ${a.call}. Good to hear you again, ${b.name}. How's the weather down your way? Over.`);
    say(1, `Hey ${a.name}! It's raining cats and dogs here in ${b.town}. My dog is hiding under the bed. Over to you. ${phon(a.call)}, this is ${phon(b.call)}.`, `Hey ${a.name}! It's raining cats and dogs here in ${b.town}. My dog is hiding under the bed. Over to you. ${a.call}, this is ${b.call}.`);
    say(0, `Ha! It's sunny up here in ${a.town}. I put up a new wire antenna in the oak tree this morning, and I bumped my head on a branch. Over.`);
    say(1, `Well, it works great. You're a solid five nine. Did your granddaughter pass her license test? Over.`);
    say(0, `She sure did! She's a Technician now, eleven years old. She already talked to a station in Texas. Over.`);
    say(1, `That's wonderful, tell her congratulations. Well, it's time for supper. Seventy-three, ${a.name}. ${phon(a.call)}, this is ${phon(b.call)}, clear.`, `That's wonderful, tell her congratulations. Well, it's time for supper. 73, ${a.name}. ${a.call}, this is ${b.call}, clear.`);
    say(0, `Seventy-three, ${b.name}. Talk to you next week. ${phon(b.call)}, this is ${phon(a.call)}, clear.`, `73, ${b.name}. Talk to you next week. ${b.call}, this is ${a.call}, clear.`);
    return { sp, lines: L, about: `${a.name} (${a.call}) in ${a.town} and ${b.name} (${b.call}) in ${b.town}, both in Kentucky.` };
  }
  if (kind === 'net') {
    const nc = person({ st: KY, ky: 1 }), c1 = person({ st: KY, ky: 1 }), c2 = person({ st: KY, ky: 1, kid: true }), c3 = person({ st: KY, ky: 1 });
    sp = [nc, c1, c2, c3];
    say(0, `Good evening. This is ${phon(nc.call)}, net control for the Bluegrass Practice Net. This net meets every Wednesday night. Are there any check-ins? Please call now.`, `Good evening. This is ${nc.call}, net control for the Bluegrass Practice Net. This net meets every Wednesday night. Are there any check-ins? Please call now.`);
    say(1, phon(c1.call), c1.call);
    say(2, phon(c2.call), c2.call);
    say(0, `I have ${phon(c1.call)} and ${phon(c2.call)}. ${phon(c1.call)}, go ahead with your check-in.`, `I have ${c1.call} and ${c2.call}. ${c1.call}, go ahead with your check-in.`);
    say(1, `Good evening, this is ${c1.name} in ${c1.town}. Nothing to report, just listening tonight. Back to net control.`);
    say(0, `Thank you, ${c1.name}. ${phon(c2.call)}, go ahead.`, `Thank you, ${c1.name}. ${c2.call}, go ahead.`);
    say(2, `Hi! This is ${c2.name}, I'm ${c2.age} years old, in ${c2.town}. This is my very first net! Back to net control.`);
    say(0, `Welcome to the net, ${c2.name}! We're glad you're here. Any more check-ins?`);
    say(3, phon(c3.call), c3.call);
    say(0, `${phon(c3.call)}, go ahead.`, `${c3.call}, go ahead.`);
    say(3, `Evening all, ${c3.name} in ${c3.town}. Just a reminder, the club picnic is Saturday at the park. Back to you.`);
    say(0, `Thanks, ${c3.name}. Hearing no more check-ins, this is ${phon(nc.call)}, closing the net. Seventy-three, everybody.`, `Thanks, ${c3.name}. Hearing no more check-ins, this is ${nc.call}, closing the net. 73, everybody.`);
    return { sp, lines: L, about: `${nc.name} (${nc.call}) is net control. Check-ins: ${c1.call}, ${c2.call} (a kid!), ${c3.call}.` };
  }
  /* kid */
  const k = person({ st: KY, ky: 1, kid: true }), o = person();
  sp = [k, o];
  say(0, `CQ CQ CQ, this is ${phon(k.call)}, ${phon(k.call)}, calling CQ.`, `CQ CQ CQ, this is ${k.call}, ${k.call}, calling CQ.`);
  say(1, `${phon(k.call)}, this is ${phon(o.call)}.`, `${k.call}, this is ${o.call}.`);
  say(0, `Hi! You're five nine. My name is ${k.name}, I'm ${k.age}, and I'm in ${k.town}, Kentucky. What's your name? ${phon(o.call)}, this is ${phon(k.call)}.`, `Hi! You're five nine. My name is ${k.name}, I'm ${k.age}, and I'm in ${k.town}, Kentucky. What's your name? ${o.call}, this is ${k.call}.`);
  say(1, `Hello ${k.name}! My name is ${o.name}, and I'm in ${o.st}. You sound great. How long have you been a ham? Over.`);
  say(0, `Two months! I passed my test at the library. This is my third contact ever! Over.`);
  say(1, `Congratulations! Keep it up, you're doing a great job. Seventy-three, ${k.name}!`, `Congratulations! Keep it up, you're doing a great job. 73, ${k.name}!`);
  say(0, `Seventy-three! Thanks, ${o.name}!`, `73! Thanks, ${o.name}!`);
  return { sp, lines: L, about: `${k.name} (${k.call}) is ${k.age} years old. ${o.name} (${o.call}) is in ${o.st}.` };
}

function cwScript(kind) {
  const P = [], s = (i, t) => P.push([i, t]);
  if (kind === 'cwcq' || kind === 'cwslow') {
    const a = person({ st: KY, ky: 1 }), b = person();
    const A = a.call, B = b.call, nb = b.name.toUpperCase(), na = a.name.toUpperCase();
    s(0, `CQ CQ CQ DE ${A} ${A} K`); s(0, `CQ CQ CQ DE ${A} ${A} K`);
    s(1, `${A} DE ${B} ${B} K`);
    s(0, `${B} DE ${A} GM TNX FER CALL = UR RST 579 579 = NAME ${na} ${na} = QTH KY = HW? ${B} DE ${A} KN`);
    s(1, `R R FB ${na} = UR 599 = NAME ${nb} = QTH ${STAB[b.st] || b.st} = TNX ES 73 ${A} DE ${B} <SK>`);
    s(0, `TU ${nb} 73 GL <SK> EE`);
    return { sp: [a, b], parts: P, wpm: kind === 'cwslow' ? 8 : 16, about: `${A} (${a.name}) is calling CQ. ${B} (${b.name}) answers.` };
  }
  if (kind === 'cwpota') {
    const a = person({ st: KY, ky: 1 }), h = [person(), person(), person()], p = pick(PARKS);
    s(0, `CQ POTA CQ POTA DE ${a.call} ${a.call} K`);
    h.forEach((x, i) => { s(i + 1, x.call); s(0, `${x.call} 5NN KY`); s(i + 1, `TU 5NN ${STAB[x.st] || 'OH'} 73`); s(0, `TU ${a.call} POTA`); });
    return { sp: [a].concat(h), parts: P, wpm: 20, about: `${a.call} is in ${p.n} (${p.c}) sending Morse code. Hunters: ${h.map(x => x.call).join(', ')}.` };
  }
  if (kind === 'cwrag') {
    const a = person({ st: KY, ky: 1 }), b = person();
    const A = a.call, B = b.call, na = a.name.toUpperCase(), nb = b.name.toUpperCase();
    s(0, `${B} DE ${A} R R FB ${nb} = WX HR SUNNY ES WARM = RIG HR IS KX2 ES ANT IS WIRE IN TREE = HW? ${B} DE ${A} KN`);
    s(1, `${A} DE ${B} R FB ${na} NICE RIG = WX HR RAIN = MY DOG IS BARKING AT THUNDER HI HI = ${A} DE ${B} KN`);
    s(0, `R HI HI = OK ${nb} TNX FER QSO = 73 ES CUL ${B} DE ${A} <SK>`);
    s(1, `TU ${na} 73 <SK> EE`);
    return { sp: [a, b], parts: P, wpm: 18, about: `${a.name} (${A}) in Kentucky and ${b.name} (${B}) in ${b.st} are chatting in Morse.` };
  }
  /* cwsota */
  const a = person({ st: KY, ky: 1 }), b = person(), sa = pick(SUMMITS), sb = 'W4C/WM-' + String(rnd(1, 99)).padStart(3, '0');
  s(0, `CQ SOTA DE ${a.call}/P K`);
  s(1, `S2S ${b.call}/P`);
  s(0, `${b.call} 559 559 ${sa.c}`);
  s(1, `R TU 579 ${sb} ${sb} 73`);
  s(0, `TU 73 EE`);
  return { sp: [a, b], parts: P, wpm: 17, about: `${a.call} is on ${sa.n} (${sa.c}). ${b.call} is on another summit, ${sb}.` };
}

/* ---------------- Morse timing ---------------- */
const MC = { A: '.-', B: '-...', C: '-.-.', D: '-..', E: '.', F: '..-.', G: '--.', H: '....', I: '..', J: '.---', K: '-.-', L: '.-..', M: '--', N: '-.', O: '---', P: '.--.', Q: '--.-', R: '.-.', S: '...', T: '-', U: '..-', V: '...-', W: '.--', X: '-..-', Y: '-.--', Z: '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.', '/': '-..-.', '?': '..--..', '=': '-...-', '<BT>': '-...-', '<SK>': '...-.-', '<KN>': '-.--.', '.': '.-.-.-', ',': '--..--' };
function tokens(t) { const out = []; const re = /<[A-Z]{2}>|\S|\s+/g; let m; while ((m = re.exec(t))) out.push(m[0]); return out; }
/* returns {els:[[start,dur]], chars:[[time, text]], len} in seconds */
function morse(text, wpm) {
  const cw = Math.max(wpm, 13), u = 1.2 / cw, fw = wpm < cw ? (60 / wpm - 37.2 * u) / 19 : u; // Farnsworth spacing when slow
  let t = 0; const els = [], chars = [];
  tokens(text).forEach(tk => {
    if (/^\s+$/.test(tk)) { t += 7 * fw - 3 * fw; chars.push([t, ' ']); return; }
    const code = MC[tk]; if (!code) return;
    code.split('').forEach((e, i) => { const d = e === '.' ? u : 3 * u; els.push([t, d]); t += d + (i < code.length - 1 ? u : 0); });
    chars.push([t, tk === '=' ? ' = ' : tk]); t += 3 * fw;
  });
  return { els, chars, len: t };
}

/* ---------------- bands ---------------- */
const BANDS = {
  40: { lo: 7000000, hi: 7300000, cwTop: 7125000, sb: 'LSB', start: 7200000,
    cw: [['cwcq', 7028, 7045], ['cwpota', 7055, 7066], ['cwrag', 7035, 7050], ['cwslow', 7100, 7118]],
    talk: [['pota', 7185, 7200], ['rag', 7230, 7245], ['net', 7255, 7262], ['kid', 7270, 7285], ['p2p', 7205, 7220]] },
  20: { lo: 14000000, hi: 14350000, cwTop: 14150000, sb: 'USB', start: 14285000,
    cw: [['cwcq', 14020, 14035], ['cwpota', 14056, 14064], ['cwrag', 14038, 14050], ['cwsota', 14066, 14075]],
    talk: [['pota', 14250, 14262], ['p2p', 14300, 14315], ['kff', 14240, 14246], ['sota', 14335, 14345], ['rag', 14200, 14215], ['kid', 14270, 14282]] }
};
let band = 20, dial = BANDS[20].start, on = false, stations = [];
const S = store.get('kpcKidsRadio', { found: [], vol: 0.8, words: true, band: 20 });
if (!Array.isArray(S.found)) S.found = [];
const save = () => store.set('kpcKidsRadio', S);

/* ---------------- audio ---------------- */
let AC = null, master, sigBus, noiseG, mumbleG, crashG, analyser, abuf;
function audio() {
  if (AC) { if (AC.state === 'suspended') AC.resume(); return; }
  AC = new (window.AudioContext || window.webkitAudioContext)();
  master = AC.createGain(); master.gain.value = S.vol; master.connect(AC.destination);
  sigBus = AC.createGain(); sigBus.connect(master);
  analyser = AC.createAnalyser(); analyser.fftSize = 512; sigBus.connect(analyser); abuf = new Float32Array(analyser.fftSize);
  const len = AC.sampleRate * 2, b = AC.createBuffer(1, len, AC.sampleRate), d = b.getChannelData(0); for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
  const mk = (type, f, q, g) => { const s = AC.createBufferSource(); s.buffer = b; s.loop = true; const fl = AC.createBiquadFilter(); fl.type = type; fl.frequency.value = f; fl.Q.value = q; const gn = AC.createGain(); gn.gain.value = g; s.connect(fl); fl.connect(gn); gn.connect(master); s.start(); return gn; };
  noiseG = mk('bandpass', 1500, 0.5, 0);
  mumbleG = mk('bandpass', 550, 1.8, 0);
  crashG = mk('lowpass', 900, 0.7, 0);
}
function setNoise(level) { if (noiseG) noiseG.gain.setTargetAtTime(on ? level : 0, AC.currentTime, 0.08); }

/* ---------------- voices ---------------- */
let VO = [], lastCancel = 0;
const ANDROID = /Android/i.test(navigator.userAgent);
const MALE = /\b(male|man|david|mark|guy|daniel|fred|alex|tom|aaron|arthur|george|james|rishi|eddy|reed|ralph|bruce|junior|lee|oliver|thomas)\b/i;
function loadVoices() {
  const v = (window.speechSynthesis && speechSynthesis.getVoices()) || [];
  VO = v.filter(x => /^en[-_]/i.test(x.lang));
  if (ANDROID) { const loc = VO.filter(x => x.localService); if (loc.length) VO = loc; }
  if (!VO.length) VO = v;
}
if (window.speechSynthesis) { loadVoices(); speechSynthesis.onvoiceschanged = loadVoices; }
function hush() { if (window.speechSynthesis) { speechSynthesis.cancel(); lastCancel = Date.now(); } }
/* Browser voices can get stuck (Chrome especially): onend never fires and everything queued after it stays
   silent. So: keep a reference to the utterance (Chrome can garbage-collect it and lose its events), clear the
   queue if something is still in it, give up on a line that never starts, and cancel after a timeout. */
let CUR_U = null;
function speak(text, who, pitchMul, vol, onStart) {
  return new Promise(res => {
    if (!window.speechSynthesis) { setTimeout(() => res(false), 1500 + text.length * 60); return; }
    const go = () => {
      if (speechSynthesis.speaking || speechSynthesis.pending) { speechSynthesis.cancel(); lastCancel = Date.now(); setTimeout(go2, 200); } else go2();
    };
    const go2 = () => {
      try { speechSynthesis.resume(); } catch (e) {}
      const u = new SpeechSynthesisUtterance(text); CUR_U = u;
      if (!VO.length) loadVoices();
      if (VO.length) { const pool = VO.filter(v => who.m && !who.kid ? MALE.test(v.name) : !MALE.test(v.name)); const list = pool.length ? pool : VO; u.voice = list[who.vi % list.length]; u.lang = u.voice.lang; } else u.lang = 'en-US';
      u.rate = who.rate; u.pitch = Math.max(0.05, Math.min(2, who.pitch * pitchMul)); u.volume = Math.max(0.1, Math.min(1, vol));
      let done = false, started = false;
      const fin = stuck => { if (done) return; done = true; clearTimeout(tm); clearTimeout(t0); if (stuck) { try { speechSynthesis.cancel(); } catch (e) {} lastCancel = Date.now(); } if (CUR_U === u) CUR_U = null; res(started); };
      const tm = setTimeout(() => fin(true), 2500 + text.length * 90 / u.rate);
      const t0 = setTimeout(() => { if (!started) fin(true); }, 4000);
      u.onstart = () => { started = true; if (onStart) onStart(); };
      u.onend = () => fin(false); u.onerror = () => fin(false);
      speechSynthesis.speak(u);
    };
    setTimeout(go, Math.max(0, 150 - (Date.now() - lastCancel)));
  });
}

/* ---------------- building a band ---------------- */
function place(list, minGap) {
  const out = [];
  list.forEach(([kind, a, b]) => {
    for (let i = 0; i < 40; i++) {
      const f = rnd(a, b) * 1000 + (minGap < 4000 ? rnd(0, 9) * 100 : (Math.random() < 0.3 ? 500 : 0));
      if (out.every(o => Math.abs(o.f - f) >= minGap)) { out.push({ kind, f }); break; }
    }
  });
  return out;
}
function est(text, rate) { return 0.8 + text.split(/\s+/).length * 0.36 / rate; }
function stopBand() {
  hush(); playing = null;
  stations.forEach(st => { if (st.spk) st.spk.forEach(p => { try { p.kg.gain.cancelScheduledValues(0); p.kg.gain.value = 0; p.osc.stop(); p.osc.disconnect(); } catch (e) {} }); });
  stations = [];
}
function buildBand(keepDial) {
  stopBand(); usedCalls = new Set();
  const B = BANDS[band];
  if (!keepDial || dial < B.lo || dial > B.hi) dial = B.start;
  const now = performance.now() / 1000;
  place(B.talk, 6000).forEach(o => {
    const sc = voiceScript(o.kind);
    const st = Object.assign(o, sc, { type: 'talk', est: [], cum: [], heard: 0, s: 0.5 + Math.random() * 0.5 });
    let t = 0; sc.lines.forEach((l, i) => { st.cum[i] = t; st.est[i] = est(l[1], sc.sp[l[0]].rate); t += st.est[i] + 0.9; });
    st.total = t + 7; st.t0 = now - Math.random() * st.total; st.said = [];
    stations.push(st);
  });
  if (AC) {
    place(B.cw, 2500).forEach(o => {
      const sc = cwScript(o.kind);
      const st = Object.assign(o, sc, { type: 'cw', pi: rnd(0, sc.parts.length - 1), nextT: AC.currentTime + Math.random() * 3, chars: [], heard: 0 });
      st.spk = sc.sp.map((p, i) => {
        const osc = AC.createOscillator(), kg = AC.createGain(), pg = AC.createGain();
        osc.type = 'sine'; kg.gain.value = 0; pg.gain.value = 0;
        osc.connect(kg); kg.connect(pg); pg.connect(sigBus); osc.start();
        return { osc, kg, pg, dHz: i === 0 ? 0 : rnd(-60, 60), amp: (i === 0 ? 0.32 : 0.12 + Math.random() * 0.2), wpm: sc.wpm + (i === 0 ? 0 : rnd(-2, 3)) };
      });
      stations.push(st);
    });
  }
  tuneAudio(); draw();
}

/* ---------------- CW scheduling ---------------- */
const TONE = 650;
function cwTick() {
  if (!AC || !on) return;
  const now = AC.currentTime;
  stations.forEach(st => {
    if (st.type !== 'cw' || now + 0.5 < st.nextT) return;
    const [who, text] = st.parts[st.pi], p = st.spk[who];
    const m = morse(text, p.wpm), t0 = Math.max(st.nextT, now + 0.05);
    m.els.forEach(([a, d]) => { p.kg.gain.setTargetAtTime(1, t0 + a, 0.003); p.kg.gain.setTargetAtTime(0, t0 + a + d, 0.003); });
    st.chars.push({ t: t0, who, list: m.chars.map(([t, c]) => [t0 + t, c]), end: t0 + m.len });
    if (st.chars.length > 6) st.chars.shift();
    st.pi = (st.pi + 1) % st.parts.length;
    st.nextT = t0 + m.len + (st.pi === 0 ? 6 + Math.random() * 6 : 0.8 + Math.random() * 1.4);
  });
}
function cwTone(st, p) { const off = (st.f + p.dHz) - dial; return TONE + off; }
function pass(tone) { if (tone < 80 || tone > 2700) return 0; if (tone < 200) return (tone - 80) / 120; if (tone > 1900) return (2700 - tone) / 800; return 1; }

/* ---------------- tuning ---------------- */
function nearest(type) {
  let best = null, bd = 1e12;
  stations.forEach(st => { if (type && st.type !== type) return; const d = Math.abs(st.f - dial); if (d < bd) { bd = d; best = st; } });
  return best ? { st: best, d: bd, off: dial - best.f } : null;
}
function tuneAudio() {
  if (!AC) return;
  const t = AC.currentTime;
  stations.forEach(st => {
    if (st.type !== 'cw') return;
    st.spk.forEach(p => { const tone = cwTone(st, p); p.osc.frequency.setTargetAtTime(Math.max(40, Math.abs(tone)), t, 0.01); p.pg.gain.setTargetAtTime(on ? p.amp * pass(tone) * (st.kind === 'cwslow' ? 1.1 : 1) : 0, t, 0.02); });
  });
}
function setDial(f) {
  const B = BANDS[band];
  dial = Math.round(Math.max(B.lo, Math.min(B.hi, f)) / 10) * 10;
  tuneAudio(); draw();
}

/* ---------------- voice playback ---------------- */
let playing = null, gen = 0;
function pos(st, nowS) {
  let e = (nowS - st.t0) % st.total; if (e < 0) e += st.total;
  for (let i = 0; i < st.lines.length; i++) { const a = st.cum[i]; if (e < a) return { idx: i, inLine: false, wait: a - e }; if (e < a + st.est[i]) return { idx: i, inLine: true }; }
  return { idx: 0, inLine: false, wait: st.total - e };
}
async function play(st) {
  const g = ++gen; playing = { st, g, cap: '' };
  while (playing && playing.g === g && on) {
    const nowS = performance.now() / 1000, p = pos(st, nowS);
    if (!p.inLine) { await new Promise(r => setTimeout(r, Math.min(400, p.wait * 1000 + 30))); continue; }
    const [who, spoken, shown] = st.lines[p.idx], sp = st.sp[who];
    const off = (dial - st.f) / 1000 * (BANDS[band].sb === 'LSB' ? -1 : 1), clear = Math.abs(off) <= 0.25;
    const pm = clear ? 1 : Math.max(0.15, 1 - off * 0.55);
    playing.who = who; playing.clear = clear; playing.speaking = false;
    st.said.push({ who, text: clear ? shown : garble(shown), clear }); if (st.said.length > 8) st.said.shift();
    draw();
    const ok = await speak(spoken, sp, pm, S.vol * sp.s * (clear ? 1 : 0.75), () => { if (playing && playing.g === g) playing.speaking = true; });
    if (!playing || playing.g !== g) return;
    playing.speaking = false;
    st.t0 = performance.now() / 1000 - (st.cum[p.idx] + st.est[p.idx]);
    await new Promise(r => setTimeout(r, 700));
  }
}
function garble(t) { return t.replace(/[a-z]/gi, c => Math.random() < 0.45 ? '~' : c); }
function stopPlay() { if (playing) { gen++; playing = null; hush(); } }

/* ---------------- main loop ---------------- */
let crashT = 0, lockT = 0, lastLock = null;
function tick() {
  if (!on) return;
  cwTick();
  const nowS = performance.now() / 1000;
  const v = nearest('talk'), c = nearest('cw');
  /* voices */
  if (v && v.d <= 1600) { if (!playing || playing.st !== v.st) { stopPlay(); play(v.st); } }
  else if (playing) stopPlay();
  /* far-off mumble: a voice is close but not close enough */
  let mum = 0;
  if (v && v.d > 1600 && v.d < 3200 && pos(v.st, nowS).inLine) mum = (1 - (v.d - 1600) / 1600) * 0.35 * (0.4 + Math.random() * 0.6);
  if (mumbleG) mumbleG.gain.setTargetAtTime(mum * S.vol, AC.currentTime, 0.05);
  /* static crashes on 40 m */
  if (AC && band === 40 && nowS > crashT) { crashT = nowS + 2 + Math.random() * 7; const t = AC.currentTime; crashG.gain.setValueAtTime(0, t); crashG.gain.linearRampToValueAtTime(0.25 + Math.random() * 0.3, t + 0.01); crashG.gain.setTargetAtTime(0, t + 0.03, 0.06); }
  /* band noise dips when a strong signal is there (like a real radio's AGC) */
  const sig = meterLevel();
  setNoise((band === 40 ? 0.11 : 0.08) * (1 - Math.min(0.6, sig * 0.7)));
  /* listening to a station long enough = found it */
  const lock = lockedStation();
  if (lock && lock === lastLock) { lockT += 0.1; if (lockT > 5 && !lock.found) { lock.found = true; foundKind(lock.kind); } } else { lockT = 0; lastLock = lock; }
  drawNow(); drawMeter(sig);
}
function lockedStation() {
  const v = nearest('talk'); if (v && v.d <= 250 && playing && playing.st === v.st) return v.st;
  const c = nearest('cw'); if (c && Math.abs(cwTone(c.st, c.st.spk[0]) - TONE) < 150) return c.st;
  return null;
}
let meterSmooth = 0;
function meterLevel() {
  let lvl = 0;
  if (analyser) { analyser.getFloatTimeDomainData(abuf); let s = 0; for (let i = 0; i < abuf.length; i++) s += abuf[i] * abuf[i]; lvl = Math.min(1, Math.sqrt(s / abuf.length) * 5); }
  if (playing && playing.speaking) { const d = Math.abs(dial - playing.st.f); lvl = Math.max(lvl, playing.st.s * (1 - d / 2200) * (0.65 + Math.random() * 0.35)); }
  meterSmooth = lvl > meterSmooth ? lvl : meterSmooth * 0.82 + lvl * 0.18;
  return meterSmooth;
}

/* ---------------- found checklist ---------------- */
function addStars(n) { let s = 0; try { s = +localStorage.getItem('kpcKidsStars') || 0; localStorage.setItem('kpcKidsStars', String(s + n)); } catch (e) {} }
function foundKind(kind) {
  if (S.found.includes(kind)) return;
  S.found.push(kind); save(); addStars(1);
  const all = KIND_ORDER.every(k => S.found.includes(k));
  if (all) addStars(5);
  toast(all ? `🏆 You found ALL ${KIND_ORDER.length} kinds of stations! +5 bonus stars!` : `⭐ New find: ${KINDS[kind].icon} ${KINDS[kind].name}! +1 star`);
  drawFound();
}
let toastT;
function toast(msg) { const t = $('krToast'); if (!t) return; t.textContent = msg; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { t.hidden = true; }, 3800); }
function drawFound() {
  const box = $('krFound'); if (!box) return;
  box.innerHTML = KIND_ORDER.map(k => `<div class="kr-fb${S.found.includes(k) ? ' on' : ''}" title="${esc(KINDS[k].name)}"><span>${KINDS[k].icon}</span><small>${esc(KINDS[k].name)}</small></div>`).join('');
  const n = S.found.length; $('krFoundN').textContent = `${n} of ${KIND_ORDER.length} found`;
}
function hint() {
  const left = KIND_ORDER.filter(k => !S.found.includes(k));
  if (!left.length) { toast('You found them all! Try the other band, every station has new people each time you turn the radio on.'); return; }
  const k = pick(left);
  const b = [40, 20].find(x => BANDS[x].cw.concat(BANDS[x].talk).some(e => e[0] === k));
  const e = BANDS[b].cw.concat(BANDS[b].talk).find(x => x[0] === k);
  const lo = Math.floor(e[1] / 5) * 5, hi = Math.ceil((e[2] + 1) / 5) * 5;
  toast(`🔎 Hint: look for ${KINDS[k].icon} ${KINDS[k].name} on ${b} meters, somewhere between ${(lo / 1000).toFixed(3)} and ${(hi / 1000).toFixed(3)}. ${KINDS[k].zone === 'cw' ? 'It\'s in the Morse code zone.' : 'It\'s in the talking zone.'}`);
}

/* ---------------- drawing ---------------- */
function fmt(f) { const mhz = Math.floor(f / 1e6), khz = Math.floor(f / 1000) % 1000, h = Math.floor(f % 1000 / 10); return `${mhz}.${String(khz).padStart(3, '0')}.${String(h).padStart(2, '0')}`; }
function mode() { return dial < BANDS[band].cwTop ? 'CW' : BANDS[band].sb; }
function draw() {
  const B = BANDS[band];
  $('krFreq').textContent = on ? fmt(dial) : '';
  $('krMode').textContent = on ? mode() : '';
  $('krBandL').textContent = on ? band + ' m' : '';
  $('krZone').textContent = on ? (dial < B.cwTop ? '· · — MORSE CODE ZONE' : '🗣 TALKING ZONE') : '';
  const pct = (dial - B.lo) / (B.hi - B.lo) * 100; $('krNeedle').style.left = pct + '%';
  $('krMapCw').style.width = ((B.cwTop - B.lo) / (B.hi - B.lo) * 100) + '%';
  $('krMapLo').textContent = (B.lo / 1e6).toFixed(3); $('krMapHi').textContent = (B.hi / 1e6).toFixed(3);
  document.querySelectorAll('[data-band]').forEach(b => b.classList.toggle('on', +b.dataset.band === band));
  drawNow();
}
function drawMeter(sig) {
  const m = $('krMeter'); if (m) m.style.width = Math.round(Math.min(1, sig) * 100) + '%';
  const s = $('krS'); if (s) { const n = Math.round(Math.min(1, sig) * 9); s.textContent = n >= 9 ? 'S9+' : 'S' + Math.max(1, n); }
  const rx = $('krRx'); if (rx) rx.classList.toggle('on', sig > 0.25);
}
let lastNowKey = '';
function drawNow() {
  const box = $('krNow'); if (!box) return;
  if (!on) { if (lastNowKey !== 'off') { box.innerHTML = '<p class="kr-idle">Press the red <b>POWER</b> button to turn the radio on.</p>'; lastNowKey = 'off'; } return; }
  const v = nearest('talk'), c = nearest('cw');
  let html = '', key = '';
  const cwOk = c && Math.abs(cwTone(c.st, c.st.spk[0]) - TONE) < 150;
  const cwNear = c && pass(cwTone(c.st, c.st.spk[0])) > 0;
  if (v && v.d <= 1600 && playing && playing.st === v.st) {
    const st = v.st, K = KINDS[st.kind], clear = v.d <= 250;
    const said = st.said.slice(-4).map(x => `<div class="kr-l${x.clear ? '' : ' fz'}"><b>${esc(st.sp[x.who].call)}:</b> ${esc(x.text)}</div>`).join('');
    const words = S.words ? said || '<div class="kr-l"><i>Listening… wait for someone to talk.</i></div>' : '<div class="kr-l"><i>Words are hidden. Tap 💬 WORDS to show them.</i></div>';
    key = 'v' + st.f + st.said.length + clear + S.words;
    html = `<div class="kr-head"><span class="kr-ic">${K.icon}</span><div><h3>${esc(K.name)}</h3><p>${K.why}</p></div></div>${clear ? `<p class="kr-who">👥 ${esc(st.about)}</p>` : `<p class="kr-tune">😵 Sounds funny? Turn the dial a tiny bit ${dial > st.f ? 'DOWN ◀' : 'UP ▶'} until the voice sounds normal.</p>`}<div class="kr-cpt">${words}</div>${gloss(st.said.map(x => x.text).join(' '))}`;
  } else if (cwNear) {
    const st = c.st, K = KINDS[st.kind], now = AC.currentTime;
    const lines = st.chars.filter(p => p.t <= now).slice(-3).map(p => `<div class="kr-l cw"><b>${esc(st.sp[p.who].call)}:</b> ${esc(p.list.filter(x => x[0] <= now).map(x => x[1]).join('').replace(/<(\w\w)>/g, ' <$1> '))}${now < p.end ? '<span class="kr-cur">▌</span>' : ''}</div>`).join('');
    key = 'c' + st.f + Math.round(now * 5) + cwOk + S.words;
    if (!cwOk) html = `<div class="kr-head"><span class="kr-ic">🎵</span><div><h3>Beeps nearby!</h3><p>That's Morse code. Turn the dial slowly ${dial > st.f ? 'DOWN ◀' : 'UP ▶'} until the beep sounds like a nice middle note and the letters show up.</p></div></div>`;
    else html = `<div class="kr-head"><span class="kr-ic">${K.icon}</span><div><h3>${esc(K.name)}</h3><p>${K.why}</p></div></div><p class="kr-who">👥 ${esc(st.about)}</p><div class="kr-cpt">${S.words ? lines || '<div class="kr-l"><i>Listening… letters show up as they are sent.</i></div>' : '<div class="kr-l"><i>Letters are hidden. Tap 💬 WORDS to show them. Can you copy it by ear?</i></div>'}</div>${gloss(st.chars.map(p => p.list.filter(x => x[0] <= now).map(x => x[1]).join('')).join(' '))}`;
  } else if (v && v.d < 3200) {
    key = 'near'; html = `<div class="kr-head"><span class="kr-ic">👂</span><div><h3>Something's there…</h3><p>You can hear mumbling. A voice station is close! Keep turning the dial slowly ${dial > v.st.f ? 'DOWN ◀' : 'UP ▶'}.</p></div></div>`;
  } else {
    key = 'none' + (dial < BANDS[band].cwTop);
    html = `<div class="kr-head"><span class="kr-ic">📻</span><div><h3>Just band noise</h3><p>That shhhh sound is the band with nobody on this spot. Spin the dial, or press <b>SCAN</b> to jump to the next station. ${dial < BANDS[band].cwTop ? 'You\'re in the Morse code zone: listen for beeps.' : 'You\'re in the talking zone: listen for voices.'}</p></div></div>`;
  }
  if (key !== lastNowKey) { box.innerHTML = html; lastNowKey = key; }
}
function gloss(text) {
  if (!S.words) return '';
  const hits = GLOSS.filter(g => g[0].test(text)).slice(0, 10);
  return hits.length ? `<div class="kr-gl"><span>Ham words:</span>${hits.map(g => `<em><b>${esc(g[1])}</b> = ${esc(g[2])}</em>`).join('')}</div>` : '';
}

/* ---------------- controls ---------------- */
let scanning = 0;
function scan(dir) {
  if (!on) return;
  const cands = stations.map(s => s.f).filter(f => dir > 0 ? f > dial + 400 : f < dial - 400).sort((a, b) => dir > 0 ? a - b : b - a);
  const B = BANDS[band];
  const target = cands.length ? cands[0] : (dir > 0 ? B.lo + 500 : B.hi - 500);
  const sid = ++scanning, from = dial, dist = target - from, ms = Math.min(2600, 500 + Math.abs(dist) / 30);
  const t0 = performance.now();
  $('krScanU').classList.add('busy');
  const step = () => {
    if (sid !== scanning) return;
    const k = Math.min(1, (performance.now() - t0) / ms), e = 1 - Math.pow(1 - k, 3);
    setDial(from + dist * e);
    if (k < 1) requestAnimationFrame(step);
    else { setDial(target); $('krScanU').classList.remove('busy'); if (!cands.length) toast(dir > 0 ? 'End of the band, starting over from the bottom.' : 'Bottom of the band, starting over from the top.'); }
  };
  requestAnimationFrame(step);
}
function power() {
  on = !on;
  $('krPower').classList.toggle('on', on); $('krRig').classList.toggle('on', on);
  if (on) {
    audio();
    if (window.speechSynthesis) { try { loadVoices(); const u = new SpeechSynthesisUtterance(' '); u.volume = 0; speechSynthesis.speak(u); } catch (e) {} }
    buildBand(true); setNoise(0.08);
    clearInterval(power.iv); power.iv = setInterval(tick, 100);
  } else {
    clearInterval(power.iv); stopBand(); setNoise(0); if (mumbleG) mumbleG.gain.value = 0;
    drawMeter(0); draw();
  }
}
function setBand(b) { band = b; S.band = b; save(); scanning++; if (on) buildBand(false); else { dial = BANDS[b].start; draw(); } }

/* the knob: drag around in a circle; faster spins tune faster */
function knob() {
  const k = $('krKnob'); let last = null, lastT = 0;
  const ang = e => { const r = k.getBoundingClientRect(); return Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180 / Math.PI; };
  let rot = 0;
  const turn = deg => {
    rot += deg; $('krKnobCap').style.transform = `rotate(${rot}deg)`;
    if (!on) return;
    const now = performance.now(), dt = Math.max(1, now - lastT); lastT = now;
    const speed = Math.abs(deg) / dt * 1000; // degrees per second
    const perRev = FAST ? 40000 : speed > 500 ? 15000 : 4000;
    scanning++; setDial(dial + deg / 360 * perRev);
  };
  k.addEventListener('pointerdown', e => { e.preventDefault(); last = ang(e); lastT = performance.now(); k.setPointerCapture(e.pointerId); k.classList.add('grab'); });
  k.addEventListener('pointermove', e => { if (last == null) return; const a = ang(e); let d = a - last; if (d > 180) d -= 360; if (d < -180) d += 360; last = a; turn(d); });
  const end = () => { last = null; k.classList.remove('grab'); };
  k.addEventListener('pointerup', end); k.addEventListener('pointercancel', end);
  k.addEventListener('wheel', e => { e.preventDefault(); turn((e.deltaY < 0 ? 1 : -1) * (e.shiftKey ? 45 : 9)); }, { passive: false });
  k.addEventListener('keydown', e => { if (e.key === 'ArrowRight' || e.key === 'ArrowUp') { e.preventDefault(); turn(9); } if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') { e.preventDefault(); turn(-9); } });
}
let FAST = false;
function holdBtn(el, fn) {
  let iv, to;
  const stop = () => { clearTimeout(to); clearInterval(iv); };
  el.addEventListener('pointerdown', e => { e.preventDefault(); fn(); to = setTimeout(() => { iv = setInterval(fn, 90); }, 400); });
  ['pointerup', 'pointerleave', 'pointercancel'].forEach(t => el.addEventListener(t, stop));
  el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } });
}

function init() {
  if (!$('krRig')) return;
  band = BANDS[S.band] ? S.band : 20; dial = BANDS[band].start;
  $('krPower').addEventListener('click', power);
  document.querySelectorAll('[data-band]').forEach(b => b.addEventListener('click', () => setBand(+b.dataset.band)));
  $('krScanU').addEventListener('click', () => scan(1)); $('krScanD').addEventListener('click', () => scan(-1));
  holdBtn($('krUp'), () => { if (on) { scanning++; setDial(dial + 100); } });
  holdBtn($('krDn'), () => { if (on) { scanning++; setDial(dial - 100); } });
  const vol = $('krVol'); vol.value = Math.round(S.vol * 100);
  vol.addEventListener('input', () => { S.vol = vol.value / 100; save(); if (master) master.gain.setTargetAtTime(S.vol, AC.currentTime, 0.05); });
  const w = $('krWords'); const sw = () => { w.classList.toggle('on', S.words); w.setAttribute('aria-pressed', S.words); };
  w.addEventListener('click', () => { S.words = !S.words; save(); sw(); lastNowKey = ''; drawNow(); }); sw();
  const fb = $('krFast'); fb.addEventListener('click', () => { FAST = !FAST; fb.classList.toggle('on', FAST); fb.setAttribute('aria-pressed', FAST); });
  $('krHint').addEventListener('click', hint);
  $('krMap').addEventListener('click', e => { if (!on) return; const r = $('krMap').getBoundingClientRect(), B = BANDS[band]; scanning++; setDial(Math.round((B.lo + (e.clientX - r.left) / r.width * (B.hi - B.lo)) / 1000) * 1000); });
  $('krReset').addEventListener('click', () => { if (confirm('Clear your station finder checklist?')) { S.found = []; save(); drawFound(); } });
  knob(); draw(); drawFound(); drawNow();
  document.addEventListener('visibilitychange', () => { if (document.hidden && on) power(); });
}
window.KPCRADIO = { get dial() { return dial; }, setDial, stations: () => stations, playing: () => playing, power: () => on, scan, band: () => band };
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
