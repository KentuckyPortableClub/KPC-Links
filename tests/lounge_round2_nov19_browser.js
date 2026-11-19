/* Browser check for the Nov 19 Lounge round, stage 2 (the KPC app's transmit-safety and Fox & Hound work, ported to the VIP FT8 tab
   kpc-logger-ft8.js + the Lounge radio card kpc-hunt-x.js + the new kpc-onair.js). On kpc-hunt.html (VIP). FABLE REVIEWS BEFORE LIVE.
   Run:  python3 -m http.server 8795 &   BASE=http://127.0.0.1:8795/ NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules node tests/lounge_round2_nov19_browser.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8795/';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { try { if (await fn()) return true; } catch (e) {} await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic|geolocation|Geolocation/i;
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['microphone'] });
  await ctx.route(/api\.pota\.app|sota|spothole/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
  await ctx.addInitScript(([vip]) => { localStorage.setItem('kpcVipOK', vip); localStorage.setItem('kpcMyCall', '"K4TEST"'); localStorage.setItem('kpcHuntQSO', JSON.stringify({ v: 1, u: 0, grid: 'EM77', q: [] })); localStorage.setItem('kpcLgSet', JSON.stringify({ call: 'K4TEST', grid: 'EM77' })); if (!sessionStorage.__i) { sessionStorage.__i = 1; localStorage.removeItem('kpcFt8'); } }, [VIP]);
  const P = await ctx.newPage(); const errs = [];
  P.on('pageerror', e => { if (!NET.test(e.message)) errs.push('PE ' + e.message); }); P.on('dialog', d => d.accept());
  await P.goto(BASE + 'kpc-hunt.html');
  ok(await until(() => P.evaluate(() => !!window.KPCFt8Tab), 8000), 'VIP page: the FT8 tab script is there');
  await P.evaluate(() => { const x = [...document.querySelectorAll('.rt-f8,[data-ft8open]')].find(e => e.offsetParent !== null) || document.querySelector('[data-ft8open]'); x.click(); }); await sleep(800);
  const F = (fn, a) => P.evaluate(fn, a);

  console.log('HALT HOLDS');
  await F(() => document.getElementById('f8Cq').click()); await sleep(200);
  let r = await F(() => [KPCFt8Tab.txOn(), KPCFt8Tab._held()]);
  ok(r[0] === true && r[1] === false, '📣 CQ: TX on, not held');
  await F(() => document.getElementById('f8Halt').click()); await sleep(100);
  await F(() => KPCFt8Tab._feed(1001, [{ text: 'K4TEST Q4ABC EM78', db: -8, hz: 1500 }])); await sleep(200);
  r = await F(() => [KPCFt8Tab.txOn(), KPCFt8Tab._held(), KPCFt8Tab.qso().dx]);
  ok(r[0] === false && r[1] === true, 'HALT, then a station answers the CQ: TX STAYS OFF (it used to switch itself back on) · dx ' + r[2]);
  await F(() => document.getElementById('f8En').click()); await sleep(100);
  r = await F(() => [KPCFt8Tab.txOn(), KPCFt8Tab._held()]);
  ok(r[0] === true && r[1] === false, 'ENABLE TX by the operator: on again');
  await F(() => KPCFt8Tab._feed(1003, [{ text: 'K4TEST Q4ABC R-05', db: -8, hz: 1500 }])); await sleep(150);
  r = await F(() => KPCFt8Tab.txOn());
  ok(r === true, 'not held: the contact carries on as before');
  await F(() => document.getElementById('f8Halt').click());

  console.log('NEVER OFF ITS OWN DIAL');
  await F(() => KPCFt8Tab._lastR(14243, 'USB'));
  r = await F(() => KPCFt8Tab._offDial());
  ok(r === true, 'the radio read on 14.243 USB while FT8 is on 14.074 = off its dial');
  await F(() => document.getElementById('f8En').click()); await sleep(100);
  r = await F(() => [KPCFt8Tab.txOn(), KPCFt8Tab._notes().slice(-1)[0] || '']);
  ok(r[0] === false && /14\.2430/.test(JSON.stringify(r[1])), 'ENABLE TX there: refused with the reason (and the radio is asked to tune back)');
  await F(() => KPCFt8Tab._lastR(14074, 'DATA-U'));
  r = await F(() => KPCFt8Tab._offDial());
  ok(r === false, 'back on 14.074 DATA: fine');

  r = await F(() => [KPCFt8Tab._knobOk({ khz: 14243, mode: 'USB' }), KPCFt8Tab._knobOk({ khz: 14090, mode: 'USB' }), KPCFt8Tab._knobOk({ khz: 14200, mode: 'DATA' }), KPCFt8Tab._knobOk({ khz: 14076, mode: 'CW' })]);
  ok(r.join() === 'false,true,true,false', 'knob follow: voice frequency in USB no; 14.090 in USB yes (Icom reads USB-D as USB); DATA yes; CW no');
  console.log('FOX & HOUND');
  await F(() => { const h = document.getElementById('f8Hound'); h.checked = true; h.dispatchEvent(new Event('change')); }); await sleep(100);
  await F(() => KPCFt8Tab._feed(1010, [{ text: 'CQ VP8A FD86', db: -12, hz: 400 }, { text: 'Q4XYZ RR73; Q4OLD <VP8A> -15', db: -12, hz: 400 }])); await sleep(300);
  r = await F(() => Object.keys(KPCFt8Tab._foxes()));
  ok(r.includes('VP8A'), 'the Fox is spotted from its two-in-one message');
  const id = await F(() => { const x = KPCFt8Tab.lines().find(l => l.text === 'CQ VP8A FD86'); return x && x.id; });
  await F(i => KPCFt8Tab.pick(i), id); await sleep(200);
  r = await F(() => [KPCFt8Tab.qso().hound, KPCFt8Tab.S.txHz, KPCFt8Tab.qso().next, KPCFt8Tab.txOn()]);
  ok(r[0] === true && r[1] >= 1000 && r[2] === 1 && r[3] === true, 'tap the Fox: HOUND, calling above 1000 Hz (' + r[1] + ') with Tx1 (grid)');
  await F(() => KPCFt8Tab._feed(1012, [{ text: 'K4TEST VP8A -12', db: -9, hz: 400 }])); await sleep(200);
  r = await F(() => [KPCFt8Tab.qso().next, KPCFt8Tab.S.txHz, KPCFt8Tab.qso().rs, KPCFt8Tab.qso().rr]);
  ok(r[0] === 3 && r[1] === 400 && r[2] === '-09' && r[3] === '-12', 'the Fox answers: R+report AT the Fox\'s frequency (Tx3 at ' + r[1] + ' Hz, sent ' + r[2] + ', rcvd ' + r[3] + ')');
  await F(() => KPCFt8Tab._feed(1014, [{ text: 'K4TEST RR73; Q4NEXT <VP8A> -11', db: -9, hz: 400 }])); await sleep(300);
  r = await F(() => [KPCFt8Tab.qso().state, KPCFt8Tab.txOn(), JSON.parse(localStorage.getItem('kpcHuntQSO') || '{}').q.map(q => q.call || q.c).join()]);
  ok(r[0] === 'done' && r[1] === false && /VP8A/.test(r[2]), 'the Fox sends RR73 in its two-in-one message: logged, TX off, no 73 (' + r[2] + ')');
  await F(() => KPCFt8Tab._feed(1016, [{ text: 'K4TEST RR73; Q4MORE <VP8A> -11', db: -9, hz: 400 }])); await sleep(200);
  r = await F(() => JSON.parse(localStorage.getItem('kpcHuntQSO') || '{}').q.filter(q => /VP8A/.test(q.call || q.c || '')).length);
  ok(r === 1, 'the Fox repeating RR73 is not logged twice');

  console.log('ON AIR + STOP ALL');
  ok(await until(() => F(() => !!window.KPCOnAir), 4000), 'kpc-onair.js loaded by the scripts themselves');
  r = await F(() => KPCOnAir.busy());
  ok(Array.isArray(r) && r.length === 0, 'nothing on the air: no banner');
  await F(() => { window.__stopped = 0; KPCOnAir.add('t', { label: 'test sender', busy: () => !window.__stopped, stop: () => { window.__stopped = 1; } }); }); await sleep(400);
  r = await F(() => { const e = document.getElementById('kpcOnAir'); return [!!e && !e.hidden, e && e.textContent]; });
  ok(r[0] && /ON AIR/.test(r[1]) && /test sender/.test(r[1]) && /STOP ALL/.test(r[1]), 'something sending: ● ON AIR … test sender · ■ STOP ALL');
  await P.keyboard.press('Escape'); await sleep(400);
  r = await F(() => [window.__stopped, document.getElementById('kpcOnAir').hidden]);
  ok(r[0] === 1 && r[1], 'Esc = STOP ALL: every sender told to stop, banner gone');
  r = await F(() => Object.keys(KPCOnAir).length && ['ft8'].every(k => true));
  await F(() => KPCOnAir.remove('t'));
  ok(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
  await b.close(); console.log(`\n${passes} passed, ${fails} failed`); process.exit(fails ? 1 : 0);
})();
