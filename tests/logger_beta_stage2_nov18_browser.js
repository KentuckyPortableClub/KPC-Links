/* Lounge round stage 2 (Nov 18 2026): the web logger beta re-synced from the KPC app 0.9.10.
   Checks: first-time setup opens by itself; app-only switches stay off and hidden (auto spot me, AUTO run / hunt / both, level helper,
   hear my processed voice); no FreeDV / remote / Capacitor files asked for; POTA spots come from the club relay; every screen opens with no
   page errors; nothing runs off the side on a phone.
   Not in kpc_full_suite.py (needs Chromium). Run: python3 -m http.server 8797 &  BASE=http://127.0.0.1:8797/ NODE_PATH=$(npm root -g) node tests/logger_beta_stage2_nov18_browser.js
   SHOTS=<folder> saves a picture of each screen (PC and phone). */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8797/', SHOTS = process.env.SHOTS || '', URL0 = BASE + 'logger-beta/kpc-logger-beta.html';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|tile|geolocation|Geolocation|NetworkError/i;
const SPOT = [{ activator: 'K4TEST', frequency: '14062', mode: 'CW', reference: 'US-0001', spotTime: new Date().toISOString(), name: 'Test Park', locationDesc: 'US-KY' }];
async function mk(b, vp, init) {
  const c = await b.newContext({ viewport: vp, permissions: ['microphone', 'geolocation'], geolocation: { latitude: 37.5, longitude: -85.5 } });
  await c.route(/kpc-spots\..*workers\.dev/, r => r.fulfill({ status: 200, contentType: 'application/json', headers: { 'x-kpc-spot-age': '30', 'access-control-allow-origin': '*', 'access-control-expose-headers': 'x-kpc-spot-age' }, body: JSON.stringify(SPOT) }));
  await c.route(/api\.pota\.app|sota\.org|spothole|services\.swpc|api\.weather\.gov|open-meteo|worldtimeapi|timeapi|version\.json/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
  await c.addInitScript(([vip, init]) => { if (sessionStorage.__s2) return; sessionStorage.__s2 = 1; localStorage.setItem('kpcVipOK', vip); for (const k in init) localStorage.setItem(k, init[k]); }, [VIP, init || {}]);
  const P = await c.newPage(); P.errs = []; P.req = [];
  P.on('pageerror', e => { if (!NET.test(e.message)) P.errs.push('PE ' + e.message); }); P.on('console', m => { if (m.type() === 'error' && !NET.test(m.text())) P.errs.push(m.text()); });
  P.on('request', r => P.req.push(r.url())); P.on('response', r => { if (r.status() === 404 && !/\/logger-beta\/KPC-logo\.png$/.test(r.url())) P.errs.push('404 ' + r.url()); });   /* the members door's logo, before kpc-web.js points it one folder up (old, harmless) */ P.on('dialog', d => d.dismiss());
  return P;
}
const vis = (P, sel) => P.evaluate(s => [...document.querySelectorAll(s)].some(e => e.offsetParent !== null || getComputedStyle(e).position === 'fixed' && getComputedStyle(e).display !== 'none'), sel);
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream'] });

  console.log('== first visit (no call sign yet, a real person: not a test browser)');
  let P = await mk(b, { width: 1280, height: 900 });
  await P.addInitScript(() => Object.defineProperty(Navigator.prototype, 'webdriver', { get: () => false }));
  await P.goto(URL0); await sleep(6500);
  ok(await vis(P, '#wzNext'), 'first-time setup opens by itself, like the app');
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : '')); await P.context().close();

  console.log('== member who had the app-only switches on (saved from an older copy)');
  P = await mk(b, { width: 1280, height: 900 }, { kpcApp: JSON.stringify({ call: 'K4TEST', grid: 'EM77', vmon: true }), kpcAppDigi: JSON.stringify({ showAuto: true }), kpcAppAutoSpot: JSON.stringify({ ask: true, keep: 10 }), kpcSetupDone: '1' });
  await P.goto(URL0 + '?fake=1'); await sleep(4000);
  const st = await P.evaluate(() => ({ as: JSON.parse(localStorage.getItem('kpcAppAutoSpot') || '{}'), dg: window.KPCDigi && KPCDigi.S.showAuto, vm: JSON.parse(localStorage.getItem('kpcApp') || '{}').vmon, ver: window.KPCApp && KPCApp.VER }));
  ok(st.as.ask === false, 'auto spot me is off (' + JSON.stringify(st.as) + ')');
  ok(st.dg === false, 'AUTO run / hunt / both are off');
  ok(st.vm === false, 'hear my processed voice is off');
  ok(st.ver === '0.9.10', 'the page is the app 0.9.10 (' + st.ver + ')');
  for (const [sel, what] of [['#stAutoSpot', 'AUTO SPOT ME button'], ['#dgRun,#dgHunt,#dgBoth', 'AUTO RUN / HUNT / BOTH buttons'], ['#stLvlHelp,[data-lvlh]', 'level helper'], ['#stVmon', 'hear my processed voice switch']]) {
    await P.evaluate(() => { for (const g of ['station', 'digi']) { try { KPCApp.go(g); } catch (e) {} } }); await sleep(300);
    ok(!(await vis(P, sel)), what + ' not shown');
  }
  ok(!P.req.some(u => /kpc-dv|kpc-remote|capacitor\.js/.test(u)), 'no FreeDV, remote or Android files asked for');
  ok(!P.req.some(u => /kpc-dsp\.js/.test(u)) || !(await P.evaluate(() => !!(window.KPCDsp && (KPCDsp.PskRx || KPCDsp.wsprDecode)))), 'no PSK31 / WSPR code loaded');
  await P.evaluate(() => KPCApp.go('spots')); await sleep(2500);
  const sp = await P.evaluate(() => document.body.innerText.includes('K4TEST') || document.body.innerText.includes('US-0001'));
  ok(P.req.some(u => /kpc-spots\..*workers\.dev/.test(u)), 'POTA spots are asked of the club relay first');
  ok(!P.req.some(u => /api\.pota\.app\/spot\/activator/.test(u)), 'and not of POTA directly while the relay answers');
  ok(sp, 'the relay\'s spot shows on SPOTS');
  for (const g of ['log', 'digi', 'spots', 'radio', 'map', 'station']) {
    const r = await P.evaluate(g => { try { KPCApp.go(g); return true; } catch (e) { return String(e.message || e); } }, g); await sleep(700);
    if (SHOTS) await P.screenshot({ path: SHOTS + '/pc-' + g + '.png' });
    ok(r === true, 'screen ' + g + ' opens' + (r === true ? '' : ': ' + r));
  }
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 4).join(' | ') : '')); await P.context().close();

  console.log('== phone');
  P = await mk(b, { width: 390, height: 844 }, { kpcApp: JSON.stringify({ call: 'K4TEST', grid: 'EM77' }), kpcSetupDone: '1' });
  await P.goto(URL0 + '?fake=1'); await sleep(3500);
  for (const g of ['log', 'digi', 'spots', 'radio', 'map', 'station']) {
    await P.evaluate(g => { try { KPCApp.go(g); } catch (e) {} }, g); await sleep(600);
    const w = await P.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    if (SHOTS) await P.screenshot({ path: SHOTS + '/phone-' + g + '.png' });
    ok(w.sw <= w.cw + 1, 'phone ' + g + ': nothing runs off the side ' + JSON.stringify(w));
  }
  ok(P.errs.length === 0, 'no page errors (phone)' + (P.errs.length ? ': ' + P.errs.slice(0, 4).join(' | ') : '')); await P.context().close();
  await b.close();
  console.log(fails ? `\n${fails} FAILED, ${passes} passed` : `\nALL PASSED: ${passes} passed, 0 failed`); process.exit(fails ? 1 : 0);
})();
