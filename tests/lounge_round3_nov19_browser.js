/* Browser check for the Nov 19 Lounge round 3 (the app's FT8 review fixes in the VIP FT8 tab, TX off when the tab is left, the BIG RADIO
   SCREEN option on the Lounge radio card + its #radio deep link, the limiter on hold to talk). FABLE REVIEWS BEFORE LIVE.
   Run:  python3 -m http.server 8795 &   BASE=http://127.0.0.1:8795/ NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules node tests/lounge_round3_nov19_browser.js */
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = process.env.BASE || 'http://127.0.0.1:8795/';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { try { if (await fn()) return true; } catch (e) {} await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic|geolocation|Geolocation/i;
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'] });
  const mk = async (guest) => { const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['microphone'] });
    await ctx.route(/api\.pota\.app|sota|spothole/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    await ctx.addInitScript(([vip, guest]) => { if (guest) { Object.defineProperty(navigator, 'webdriver', { get: () => false }); localStorage.removeItem('kpcMember'); } else localStorage.setItem('kpcVipOK', vip);
      localStorage.setItem('kpcMyCall', '"K4TEST"'); localStorage.setItem('kpcHuntQSO', JSON.stringify({ v: 1, u: 0, grid: 'EM77', q: [] })); localStorage.setItem('kpcLgSet', JSON.stringify({ call: 'K4TEST', grid: 'EM77' })); if (!sessionStorage.__i) { sessionStorage.__i = 1; localStorage.removeItem('kpcFt8'); } }, [VIP, guest]);
    const P = await ctx.newPage(); P.errs = []; P.on('pageerror', e => { if (!NET.test(e.message)) P.errs.push('PE ' + e.message); }); P.on('dialog', d => d.accept()); return P; };
  let P = await mk(false); await P.goto(BASE + 'kpc-hunt.html');
  ok(await until(() => P.evaluate(() => !!window.KPCFt8Tab), 8000), 'VIP page: FT8 tab script there');
  await P.evaluate(() => { const x = [...document.querySelectorAll('.rt-f8,[data-ft8open]')].find(e => e.offsetParent !== null) || document.querySelector('[data-ft8open]'); x.click(); }); await sleep(800);
  const F = (fn, a) => P.evaluate(fn, a);

  console.log('FT8 REVIEW FIXES');
  await F(() => KPCFt8Tab._feed(2001, [{ text: 'CQ POTA Q4ABC', db: -5, hz: 900 }])); await sleep(150);
  let r = await F(() => { const x = KPCFt8Tab.lines().find(l => l.text === 'CQ POTA Q4ABC'); return x && [x.fr, x.cqw]; });
  ok(r && r[0] === 'Q4ABC' && r[1] === 'POTA', '"CQ POTA Q4ABC" (no grid): the call is Q4ABC, not POTA (' + r + ')');
  await F(() => document.getElementById('f8Cq').click()); await sleep(150);
  await F(() => KPCFt8Tab._feed(2003, [{ text: 'K4TEST Q4ZZZ RR73', db: -5, hz: 900 }])); await sleep(150);
  r = await F(() => [KPCFt8Tab.qso().dx, JSON.parse(localStorage.getItem('kpcHuntQSO') || '{}').q.length]);
  ok(r[0] !== 'Q4ZZZ' && r[1] === 0, 'while calling CQ, a stray "K4TEST Q4ZZZ RR73" does not start a contact or log one');
  const src = fs.readFileSync('kpc-logger-ft8.js', 'utf8');
  ok(/your clock is about \$\{Math\.abs\(m\)\.toFixed\(1\)\} s \$\{m > 0 \? 'fast' : 'slow'\}/.test(src), 'clock hint: DT + = your clock is FAST (was the other way round)');
  ok(/const done = \(\) => \{ if \(TXSRC !== src\) return; stopTx\(\);\s*if \(n === 4\)/.test(src), 'RR73 / 73 logged only once the message has gone out to the end (a HALT part-way logs nothing)');
  r = await F(() => KPCFt8Tab.txOn()); ok(r === true, 'CQ: TX armed');
  await F(() => document.getElementById('f8Back').click()); await sleep(200);
  r = await F(() => [KPCFt8Tab.txOn(), KPCFt8Tab._held()]);
  ok(r[0] === false && r[1] === true, 'leave the FT8 screen: TX is switched off and held (it used to stay armed)');

  console.log('LOUNGE RADIO CARD');
  ok(P.errs.length === 0, 'no page errors on the VIP page' + (P.errs.length ? ': ' + P.errs.slice(0, 2).join(' | ') : ''));
  await P.context().close(); P = await mk(false); await P.goto(BASE + 'kpc-hunters.html'); await sleep(2500);   /* the VIP page draws the card only inside its ⚙ pop-up */
  r = await P.evaluate(() => { const a = document.querySelector('.lr-big'); return a && [a.getAttribute('href'), a.textContent]; });
  ok(r && /logger-beta\/kpc-logger-beta\.html#radio/.test(r[0]) && /BIG RADIO SCREEN/.test(r[1]), 'member: 🖤 BIG RADIO SCREEN (beta) on the radio card → the beta logger\'s RADIO screen');
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 2).join(' | ') : ''));
  await P.context().close();
  P = await mk(true); await P.goto(BASE + 'kpc-hunters.html'); await sleep(2500);
  r = await P.evaluate(() => [...document.querySelectorAll('a[href*="logger-beta"]')].filter(a => a.offsetParent !== null).length);
  ok(r === 0, 'guest on the public Hunters Lounge: no link to the members-only beta logger is shown');
  await P.context().close();
  P = await mk(false); await P.goto(BASE + 'logger-beta/kpc-logger-beta.html?fake=1#radio');
  r = await until(() => P.evaluate(() => document.body.dataset.screen === 'radio'), 12000);
  ok(r, 'the beta logger opened with #radio lands on the RADIO screen');
  await P.context().close();

  console.log('HOLD TO TALK LIMITER');
  const hx = fs.readFileSync('kpc-hunt-x.js', 'utf8');
  ok(/vg\.connect\(lim\); lim\.connect\(lg\); lg\.connect\(sc\); sc\.connect\(gate\)/.test(hx) && /lim\.threshold\.value = -3/.test(hx), 'the voice goes through a −3 dB 20:1 limiter and a soft clip before the gate');
  await b.close(); console.log(`\n${passes} passed, ${fails} failed`); process.exit(fails ? 1 : 0);
})();
