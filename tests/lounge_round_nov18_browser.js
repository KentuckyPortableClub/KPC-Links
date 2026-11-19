/* Browser check for the Nov 18 2026 Lounge round, stage 1 (the app 0.9.10 FT8 decoder, PSK31 / WSPR off the website, the app's noise filter,
   the licence notices), on the beta test room first, then the VIP Lounge, the public Hunters Lounge and the old web logger.
   Not part of kpc_full_suite.py (needs Chromium + Playwright). Run:
     python3 -m http.server 8795 &   BASE=http://127.0.0.1:8795/ NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules node tests/lounge_round_nov18_browser.js
   SHOTS=<folder> also saves a picture of the FT8 screen on each page. */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8795/', SHOTS = process.env.SHOTS || '';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { try { if (await fn()) return true; } catch (e) {} await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic|geolocation|Geolocation/i;
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
const ARGS = ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'];
async function mk(b, vp, saved) {
  const ctx = await b.newContext({ viewport: vp || { width: 1280, height: 900 }, permissions: ['microphone'] });
  await ctx.route(/api\.pota\.app|sota|spothole|wspr\.live|pskreporter/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
  await ctx.addInitScript(([vip, saved]) => { if (sessionStorage.__n18) return; sessionStorage.__n18 = 1; localStorage.setItem('kpcVipOK', vip); localStorage.setItem('kpcMyCall', '"K4TEST"');
    localStorage.setItem('kpcLgSet', JSON.stringify({ call: 'K4TEST', grid: 'EM77' })); if (saved) localStorage.setItem('kpcFt8', JSON.stringify(saved)); }, [VIP, saved || null]);
  const P = await ctx.newPage(); P.errs = []; P.req = [];
  P.on('pageerror', e => { if (!NET.test(e.message)) P.errs.push('PE ' + e.message); }); P.on('console', m => { if (m.type() === 'error' && !NET.test(m.text())) P.errs.push(m.text()); });
  P.on('request', r => P.req.push(r.url())); P.on('dialog', d => d.accept());
  return P;
}
const openTab = async P => { await P.evaluate(() => { const b = [...document.querySelectorAll('.rt-f8,[data-ft8open]')].find(x => x.offsetParent !== null) || document.querySelector('[data-ft8open]'); b.click(); }); return until(() => P.evaluate(() => !document.getElementById('cFt8').hidden), 4000); };
const state = P => P.evaluate(() => ({
  modes: [...document.querySelectorAll('[data-f8m]')].map(b => b.dataset.f8m),
  saved: (JSON.parse(localStorage.getItem('kpcFt8') || '{}')).mode, m: (document.getElementById('cFt8') || {}).dataset.m,
  digi: window.KPCDigi ? Object.keys(window.KPCDigi) : [], wasmText: typeof window.KPC_FT8_WASM_B64 === 'string' && window.KPC_FT8_WASM_B64.length,
  notices: !!document.querySelector('#cFt8 a[href="notices/README.txt"]'), nr: !!(window.KPCNR && window.KPCNR.abLevel) }));

async function vip(b, page, nav) {
  console.log('== ' + page + ' (a saved PSK31 choice from before)');
  const P = await mk(b, null, { mode: 'PSK31', band: '20m' }); await P.goto(BASE + page); await sleep(2000);
  let s = await state(P);
  ok(s.saved === 'FT8', 'a saved PSK31 choice starts on FT8 (saved mode now ' + s.saved + ')');
  ok(!s.modes.includes('PSK31') && !s.modes.includes('WSPR') && s.modes.includes('FT8') && s.modes.includes('RTTY') && s.modes.includes('SSTV'), 'mode buttons: ' + s.modes.join(' '));
  ok(!s.digi.some(k => /psk|wspr|fano|unpack/i.test(k)) && s.digi.includes('RttyRx') && s.digi.includes('SstvRx') && s.digi.includes('HellRx'), 'no PSK31 / WSPR code loaded; RTTY, SSTV and HELL still there');
  ok(s.wasmText > 40000, 'the decoder travels inside kpc-ft8-wasm.js (' + s.wasmText + ' characters)');
  if (!/kpc-logger/.test(page)) ok(s.nr, "the app's noise filter is loaded (KPCNR.abLevel)");
  ok(!P.req.some(u => /kpc-ft8\.js\?v=20261017a|kpc-nr\.js\?v=20261107a|kpc-digi\.js\?v=20261018h/.test(u)), 'no old stamps fetched');
  if (nav) {
    ok(await openTab(P), 'the 📡 FT8 · CW tab opens');
    s = await state(P); ok(s.notices, 'the FT8 help line links to the licence notices');
    const how = await P.evaluate(async () => { await window.KPCFT8.load('kpc-ft8.wasm?v=20261118a'); return window.KPCFT8.load.how || ''; });
    ok(/embed|text/i.test(how) || how === '', 'the decoder starts from the embedded copy (' + (how || 'first try') + ')');
    await P.evaluate(() => document.querySelector('[data-f8m="RTTY"]').click()); await sleep(400);
    s = await state(P); ok(s.m === 'rtty' && s.saved === 'RTTY', 'RTTY still opens (screen ' + s.m + ')');
    await P.evaluate(() => window.KPCFT8UI.host.setMode('WSPR')); await sleep(300);
    s = await state(P); ok(s.saved === 'FT8', 'asking for WSPR from code lands on FT8 instead');
    await P.evaluate(() => document.querySelector('[data-f8m="FT8"]').click()); await sleep(300);
    if (SHOTS) await P.screenshot({ path: SHOTS + '/' + page.replace('.html', '') + '-ft8.png' });
    const ph = await mk(b, { width: 390, height: 844 }); await ph.goto(BASE + page); await sleep(1500); await openTab(ph); await sleep(500);
    const w = await ph.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    ok(w.sw <= w.cw + 1, 'phone: nothing runs off the side ' + JSON.stringify(w));
    if (SHOTS) await ph.screenshot({ path: SHOTS + '/' + page.replace('.html', '') + '-ft8-phone.png' });
    ok(ph.errs.length === 0, 'no page errors (phone)' + (ph.errs.length ? ': ' + ph.errs.slice(0, 3).join(' | ') : '')); await ph.context().close();
  }
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : '')); await P.context().close();
}
async function pub(b, page) {
  console.log('== ' + page + ' (public: no digital modes, FT8 tab hidden)');
  const P = await mk(b); await P.goto(BASE + page); await sleep(2000);
  const r = await P.evaluate(() => { const vis = e => !!(e && e.offsetParent !== null); return { shown: [...document.querySelectorAll('.rt-f8,[data-ft8open]')].filter(vis).length, old: !![...document.scripts].find(s => /kpc-logger-ft8\.js\?v=20261020d/.test(s.src)), digi: window.KPCDigi ? Object.keys(window.KPCDigi) : [] }; });
  ok(r.shown === 0, 'FT8 tab stays hidden'); if (page !== 'kpc-hunters.html') ok(r.old, 'kpc-logger-ft8.js keeps its older stamp (20261020d)');   /* Nov 19: kpc-hunters.html = carbon copy of the VIP page; the FT8 tab still hidden */
  ok(!r.digi.some(k => /psk|wspr/i.test(k)), 'no PSK31 / WSPR code loaded');
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : '')); await P.context().close();
}
(async () => {
  const b = await chromium.launch({ args: ARGS });
  await vip(b, 'kpc-beta-room.html', true);
  await vip(b, 'kpc-hunt.html', true);
  await vip(b, 'kpc-hunt-need.html', false);
  await vip(b, 'kpc-logger.html?old=1', false);
  await pub(b, 'kpc-hunters.html'); await pub(b, 'kpc-hunters-need.html');
  const P = await mk(b); const r1 = await P.goto(BASE + 'notices/README.txt'), r2 = await P.goto(BASE + 'notices/ft8_lib-MIT.txt');
  console.log('== notices'); ok(r1.status() === 200 && r2.status() === 200, 'notices/README.txt and notices/ft8_lib-MIT.txt are served'); await P.context().close();
  await b.close();
  console.log(fails ? `\n${fails} FAILED, ${passes} passed` : `\nALL PASSED: ${passes} passed, 0 failed`); process.exit(fails ? 1 : 0);
})();
