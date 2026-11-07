/* Tests for the Hunters Lounge radio additions (kpc-lounge-radio.js + kpc-cat.js raw/setTap + kpc-nr.js), Nov 7 2026.
   A pretend IC-7300 on a pretend USB port answers CAT, meters (SWR high) and sends scope frames.
   Run: python3 -m http.server 8770 -d <KPC-Links> &  NODE_PATH=$(npm root -g) node lounge-radio.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8770/';
let fails = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (!c) fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { if (await fn()) return true; await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined/i;
const MOCK = () => {
  const bcdLE = (n, len) => { const s = String(n).padStart(len * 2, '0'); const o = []; for (let j = len - 1; j >= 0; j--) o.push(parseInt(s.substr(j * 2, 2), 16)); return o; };
  let freq = 14074000; const q = [], wrote = []; let scope = false;
  window.__rig = { wrote, swr: 0x0010, setFreq: f => { freq = f; } };
  const port = { getInfo: () => ({ usbVendorId: 0x10C4, usbProductId: 0xEA60 }), async open() {}, async setSignals() {}, async close() {},
    readable: { getReader() { return { read: async () => { await new Promise(r => setTimeout(r, 15)); if (!q.length) return { value: new Uint8Array(0), done: false }; return { value: new Uint8Array(q.splice(0, q.length)), done: false }; }, cancel: async () => {}, releaseLock() {} }; } },
    writable: { getWriter() { return { write: async bb => { const a = Array.from(bb); wrote.push(a.map(x => x.toString(16).padStart(2, '0')).join(' '));
      for (let i = 0; i + 4 < a.length; i++) if (a[i] === 0xFE && a[i + 1] === 0xFE && a[i + 2] === 0x94) { const c = a[i + 4];
        if (c === 0x03) q.push(0xFE, 0xFE, 0xE0, 0x94, 0x03, ...bcdLE(freq, 5), 0xFD);
        else if (c === 0x04) q.push(0xFE, 0xFE, 0xE0, 0x94, 0x04, 0x01, 0x01, 0xFD);
        else if (c === 0x05) { let s = ''; for (let j = 4; j >= 0; j--) s += ((a[i + 5 + j] >> 4) * 10 + (a[i + 5 + j] & 15)).toString().padStart(2, '0'); freq = +s; q.push(0xFE, 0xFE, 0xE0, 0x94, 0xFB, 0xFD); }
        else if (c === 0x15) { const sub = a[i + 5], v = sub === 0x12 ? window.__rig.swr : sub === 0x11 ? 0x0200 : 0x0050; q.push(0xFE, 0xFE, 0xE0, 0x94, 0x15, sub, v >> 8, v & 255, 0xFD); }
        else if (c === 0x27 && a[i + 5] === 0x11) { scope = a[i + 6] === 1; q.push(0xFE, 0xFE, 0xE0, 0x94, 0xFB, 0xFD); }
        else q.push(0xFE, 0xFE, 0xE0, 0x94, 0xFB, 0xFD); } }, releaseLock() {} }; } } };
  setInterval(() => { if (!scope) return; const lo = bcdLE(freq, 5), sp = bcdLE(25000, 5); const w = []; for (let k = 0; k < 475; k++) w.push(k > 230 && k < 245 ? 140 : 20 + (k % 7));
    q.push(0xFE, 0xFE, 0xE0, 0x94, 0x27, 0x00, 0x00, 0x01, 0x01, 0x00, ...lo, ...sp, 0x00, ...w, 0xFD); }, 120);
  Object.defineProperty(navigator, 'serial', { value: { getPorts: async () => [port], requestPort: async () => port, addEventListener() {} }, configurable: true });
};
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'] }); const errs = [];
  const ctx = await b.newContext({ viewport: { width: 1100, height: 900 }, permissions: ['microphone', 'clipboard-read', 'clipboard-write'] }); const P = await ctx.newPage();
  P.on('pageerror', e => { if (!NET.test(e.message)) errs.push('PE ' + e.message); }); P.on('console', m => {  if (m.type() === 'error' && !NET.test(m.text())) errs.push(m.text()); });
  P.on('dialog', d => d.accept());
  await P.addInitScript(MOCK);
  await P.addInitScript(() => { localStorage.setItem('kpcCat', JSON.stringify({ on: true, proto: 'icom', baud: 115200, civ: '94', radio: 'ic7300', dv: 5 })); });
  await P.goto(BASE + 'kpc-hunters.html'); await sleep(1500);
  ok(await until(() => P.evaluate(() => !!window.KPCLoungeRx && !!document.getElementById('lrBox')), 6000), 'the radio card has the new part (🎛 / 📍 / 📡 / 🎧 / 📖) on the Hunters Lounge');
  let r = await P.evaluate(async () => { const c = await KPCCat.connect(true); return { c, conn: KPCCat.connected() }; });
  ok(r.conn, 'the pretend IC-7300 connects through the Lounge\'s own CONNECT');
  await P.evaluate(() => { KPCLoungeRx.draw(); document.getElementById('lrMore').open = true; });
  r = await P.evaluate(() => ({ t: document.querySelector('#lrMore summary').textContent, agc: document.querySelectorAll('[data-xc^="agc:"]').length, att: [...document.querySelectorAll('[data-xc^="att:"]')].map(b => b.textContent).join(','), split: !!document.querySelector('[data-xt="split"]'), cont: !!document.querySelector('[data-xt="contour"]'), scope: !!document.getElementById('lrScope') }));
  ok(/not checked on a real radio yet/.test(r.t) && r.agc === 4 && r.att === 'OFF,ON' && r.split && !r.cont && r.scope, 'IC-7300: AGC OFF/FAST/MID/SLOW, ATT OFF/ON, SPLIT, no CONTOUR, a SCOPE part; "not checked on a real radio yet": ' + JSON.stringify(r));
  r = await P.evaluate(async () => { __rig.wrote.length = 0; document.querySelector('[data-xt="split"]').click(); await new Promise(z => setTimeout(z, 300)); document.querySelector('[data-xc="att:20"]').click(); await new Promise(z => setTimeout(z, 300));
    document.querySelector('[data-xc="agc:slow"]').click(); await new Promise(z => setTimeout(z, 300)); const s = document.querySelector('[data-xs="shift"]'); s.value = '-400'; s.dispatchEvent(new Event('change', { bubbles: true })); await new Promise(z => setTimeout(z, 400)); return __rig.wrote.join(' | '); });
  ok(/fe fe 94 e0 0f 01 fd/.test(r) && /fe fe 94 e0 11 20 fd/.test(r) && /fe fe 94 e0 16 12 03 fd/.test(r) && /fe fe 94 e0 14 07 00 86 fd/.test(r), 'SPLIT, ATT, AGC SLOW and IF SHIFT −400 write the app\'s CI-V commands: ' + r.slice(0, 160));
  r = await P.evaluate(() => JSON.parse(localStorage.getItem('kpcLoungeRx'))); ok(r.split === 1 && r.agc === 'slow' && r.shift === -400, 'and are remembered in this browser');

  console.log('📍 BAND MEMORY');
  r = await P.evaluate(async () => { await KPCCat.tune(14285, 'USB'); await new Promise(z => setTimeout(z, 300)); await KPCCat.tune(7074, 'DATA'); await new Promise(z => setTimeout(z, 300));
    document.getElementById('lrBand').open = true; KPCLoungeRx.draw(); document.querySelector('[data-band="20m"]').click(); await new Promise(z => setTimeout(z, 800)); const r1 = await KPCCat.read();
    return { bm: JSON.parse(localStorage.getItem('kpcLoungeBM')), khz: r1 && r1.khz }; });
  ok(r.bm['20m'].khz === 14285 && r.bm['40m'].khz === 7074, 'a spot tune is remembered per band');
  ok(r.khz === 14285, 'the 20m button goes back to 14.285: ' + r.khz);

  console.log('🔧 TUNE + ⚠ SWR GUARD');
  r = await P.evaluate(async () => { __rig.wrote.length = 0; await KPCLoungeRx.tuneAsk(); return __rig.wrote.some(w => /fe fe 94 e0 1c 01 02 fd/.test(w)); });
  ok(r, '🔧 TUNE (after the "transmits a carrier" question) sends the tuner command 1C 01 02');
  r = await P.evaluate(async () => { KPCLoungeRx.X.swrMax = 2; KPCLoungeRx.X.swrAct = 'stop'; __rig.swr = 0x0120; await KPCCat.ptt(true, 'cat');
    for (let i = 0; i < 40 && !KPCLoungeRx.hold(); i++) await new Promise(z => setTimeout(z, 200));
    for (let i = 0; i < 30 && !document.getElementById('lrResume'); i++) await new Promise(z => setTimeout(z, 100));
    const held = KPCLoungeRx.hold(), unkey = __rig.wrote.some(w => /fe fe 94 e0 1c 00 00 fd/.test(w)), again = await KPCCat.ptt(true, 'cat'), res = !!document.getElementById('lrResume'), msg = (document.getElementById('lrMsg') || {}).textContent;
    document.getElementById('lrResume') && document.getElementById('lrResume').click(); __rig.swr = 0x0010; await KPCCat.ptt(false, 'cat'); return { held, unkey, again, res, msg, after: KPCLoungeRx.hold() }; });
  ok(r.held && r.unkey, 'SWR 2.6 over a 2 : 1 limit while the page keys the radio: it unkeys (1C 00 00) and holds');
  ok(r.again === false && r.after === false, 'on hold, the next transmit is refused until "OK, TRANSMIT AGAIN"');

  console.log('📡 SCOPE');
  await P.evaluate(() => { document.getElementById('lrScope').open = true; document.getElementById('lrScOn').click(); });
  ok(await until(() => P.evaluate(() => KPCLoungeRx.ROWS().length > 3), 5000), 'scope rows arrive from the radio (CI-V 27 00)');
  r = await P.evaluate(async () => { const cv = document.getElementById('lrScCv'), c = cv.getContext('2d'), d = c.getImageData(0, 0, cv.width, cv.height).data; let lit = 0; for (let i = 0; i < d.length; i += 4) if (d[i] > 120) lit++;
    const rd = await KPCCat.read(); return { lit, khz: rd && rd.khz, st: document.getElementById('lrScSt').textContent }; });
  ok(r.lit > 500 && /MHz/.test(r.st), 'it draws: ' + r.st);
  ok(r.khz === 14285, 'scope frames do not get mixed into the radio\'s answers (dial still reads 14285)');
  await P.evaluate(() => { const cv = document.getElementById('lrScCv'), b = cv.getBoundingClientRect(); cv.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: b.left + b.width * 0.75, clientY: b.top + 60 })); }); await sleep(700);
  r = await P.evaluate(async () => (await KPCCat.read()).khz); ok(r > 14285 && r < 14298, 'tap the right side of the scope = the radio goes there: ' + r);
  await P.evaluate(() => document.getElementById('lrScOn').click()); await sleep(300);

  console.log('🎧 HEAR + 📖 GUIDE + 📝 WORKS');
  r = await P.evaluate(async () => { document.getElementById('lrHear').open = true; const b = document.getElementById('lrListen'); b.click(); await new Promise(z => setTimeout(z, 1500));
    return { nr: !!document.getElementById('lrNr'), btn: document.getElementById('lrListen').textContent, live: KPCNR._live(), mode: KPCNR.S.nr }; });
  ok(r.nr && /STOP/.test(r.btn) && r.live > 0 && r.mode === 'light', '🎧 LISTEN runs the radio\'s sound through the app\'s noise clean-up (on by default: LIGHT): ' + JSON.stringify(r));
  r = await P.evaluate(async () => { document.querySelector('#lrNr [data-nrk="nr"][data-nrv="strong"]').click(); await new Promise(z => setTimeout(z, 100)); return { s: KPCNR.S.nr, on: (document.querySelector('#lrNr [data-nrv="strong"]') || {}).className }; });
  ok(r.s === 'strong' && /on/.test(r.on), 'NOISE REDUCTION STRONG picked from the Lounge');
  await P.evaluate(() => document.getElementById('lrListen').click());
  r = await P.evaluate(() => { document.getElementById('lrGuide').open = true; return document.getElementById('lrGuide').textContent; });
  ok(/94h/.test(r) && /Unlink from \[REMOTE\]/.test(r) && /DATA MOD = USB/.test(r), '📖 IC-7300 setup guide (CI-V 94h, Unlink from REMOTE, DATA MOD = USB)');
  r = await P.evaluate(async () => { document.getElementById('lrWorks').click(); document.querySelector('[data-wk="freq"][data-wv="1"]').click(); document.querySelector('[data-wk="split"][data-wv="1"]').click(); document.querySelector('[data-wk="scope"][data-wv="-1"]').click();
    document.getElementById('lrWkGo').click(); await new Promise(z => setTimeout(z, 400)); return { rep: JSON.parse(localStorage.getItem('kpcLoungeWorks')).ic7300, clip: await navigator.clipboard.readText().catch(() => '') }; });
  ok(r.rep.ok.join() === 'freq,split' && r.rep.bad.join() === 'scope' && /WORKS ON MY RADIO/.test(r.clip), '📝 report kept and copied');

  console.log('OTHER RADIOS + PAGES');
  r = await P.evaluate(() => { const o = {}; for (const id of ['ft710', 'ft891', 'ts590', 'kx3', 'g90', 'ft817']) { const c = KPCLoungeRx.caps(id); o[id] = c.keys.length; } KPCCat.pickRadio('ft710'); KPCLoungeRx.draw(); o.ftSplit = KPCLoungeRx.cmds('split', 1).map(b => new TextDecoder().decode(b)).join(); o.ftScope = !!document.getElementById('lrScope'); KPCCat.pickRadio('ic7300'); return o; });
  ok(r.ft710 > 10 && r.ft817 === 0 && r.g90 === 5 && r.ftSplit === 'ST1;' && !r.ftScope, 'per-radio list: FT-710 ' + r.ft710 + ' controls (ST1; split, no scope part), G90 5, FT-817 none');
  r = await P.evaluate(() => document.documentElement.scrollWidth - innerWidth); ok(r <= 0, 'no sideways scroll at 1100 px');
  await P.setViewportSize({ width: 390, height: 844 }); await sleep(300); r = await P.evaluate(() => document.documentElement.scrollWidth - innerWidth); ok(r <= 0, 'no sideways scroll on a phone (390 px)');
  await P.setViewportSize({ width: 1100, height: 900 });
  await P.evaluate(() => { ['lrMore', 'lrBand', 'lrScope', 'lrHear', 'lrGuide'].forEach(i => { const e = document.getElementById(i); if (e) e.open = i === 'lrMore'; }); document.getElementById('ctCat').closest('details').open = true; document.getElementById('lrBox').scrollIntoView(); });
  await sleep(300); await P.screenshot({ path: '/tmp/lounge.png' });
  for (const pg of ['kpc-hunt-cat.html', 'kpc-beta-cat.html', 'kpc-hunt.html']) { const Q = await ctx.newPage(); const pe = []; Q.on('pageerror', e => { if (!NET.test(e.message)) pe.push(e.message); }); await Q.goto(BASE + pg); await sleep(1500);
    const has = await Q.evaluate(() => ({ box: !!document.getElementById('lrBox'), card: !!document.getElementById('ctCat') })); ok(!pe.length && has.box === has.card, pg + ': loads clean' + (has.card ? ', with the new radio part' : ' (no radio card there)') + (pe.length ? ': ' + pe.join(' | ') : '')); await Q.close(); }
  ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 5).join(' | ') : ''));
  await b.close(); console.log(fails ? '\n' + fails + ' FAILED' : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
