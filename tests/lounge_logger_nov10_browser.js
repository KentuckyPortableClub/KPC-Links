/* Browser check for the Nov 10 lounge logger round (kpc-hunt-x.js + the kpc-hunt.js / kpc-lounge-radio.js / kpc-cat.js changes),
   on BOTH lounges (kpc-hunters.html public, kpc-hunt.html VIP), with no radio and with a pretend IC-7300 on a pretend USB port.
   Not part of kpc_full_suite.py (needs Chromium + Playwright). Run:
     python3 -m http.server 8799 &   NODE_PATH=$(npm root -g) node tests/lounge_logger_nov10_browser.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8799/';
let fails = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (!c) fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { if (await fn()) return true; await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic/i;
const MOCK = () => {
  const bcdLE = (n, len) => { const s = String(n).padStart(len * 2, '0'); const o = []; for (let j = len - 1; j >= 0; j--) o.push(parseInt(s.substr(j * 2, 2), 16)); return o; };
  let freq = 14285000; const q = [], wrote = [];
  window.__rig = { wrote };
  const port = { getInfo: () => ({ usbVendorId: 0x10C4, usbProductId: 0xEA60 }), async open() {}, async setSignals() {}, async close() {},
    readable: { getReader() { return { read: async () => { await new Promise(r => setTimeout(r, 15)); if (!q.length) return { value: new Uint8Array(0), done: false }; return { value: new Uint8Array(q.splice(0, q.length)), done: false }; }, cancel: async () => {}, releaseLock() {} }; } },
    writable: { getWriter() { return { write: async bb => { const a = Array.from(bb); wrote.push(a.map(x => x.toString(16).padStart(2, '0')).join(' '));
      for (let i = 0; i + 4 < a.length; i++) if (a[i] === 0xFE && a[i + 1] === 0xFE && a[i + 2] === 0x94) { const c = a[i + 4];
        if (c === 0x03) q.push(0xFE, 0xFE, 0xE0, 0x94, 0x03, ...bcdLE(freq, 5), 0xFD);
        else if (c === 0x04) q.push(0xFE, 0xFE, 0xE0, 0x94, 0x04, 0x01, 0x01, 0xFD);
        else if (c === 0x05) { let s = ''; for (let j = 4; j >= 0; j--) s += ((a[i + 5 + j] >> 4) * 10 + (a[i + 5 + j] & 15)).toString().padStart(2, '0'); freq = +s; q.push(0xFE, 0xFE, 0xE0, 0x94, 0xFB, 0xFD); }
        else if (c === 0x15) q.push(0xFE, 0xFE, 0xE0, 0x94, 0x15, a[i + 5], 0x00, 0x30, 0xFD);
        else q.push(0xFE, 0xFE, 0xE0, 0x94, 0xFB, 0xFD); } }, releaseLock() {} }; } } };
  Object.defineProperty(navigator, 'serial', { value: { getPorts: async () => [port], requestPort: async () => port, addEventListener() {} }, configurable: true });
};
(async () => {
  const b = await chromium.launch({ args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'] });
  for (const page of ['kpc-hunters.html', 'kpc-hunt.html']) {
    console.log('== ' + page);
    const errs = [];
    const ctx = await b.newContext({ viewport: { width: 1280, height: 900 }, permissions: ['microphone'] }); const P = await ctx.newPage();
    P.on('pageerror', e => { if (!NET.test(e.message)) errs.push('PE ' + e.message + ' @ ' + String(e.stack).split('\n').slice(1, 3).join(' ')); }); P.on('console', m => { if (m.type() === 'error' && !NET.test(m.text())) errs.push(m.text()); });
    P.on('dialog', d => d.accept());
    await P.addInitScript(MOCK);
    await P.addInitScript(() => { localStorage.setItem('kpcCat', JSON.stringify({ on: true, proto: 'icom', baud: 115200, civ: '94', radio: 'ic7300', dv: 5 })); localStorage.setItem('kpcMyCall', '"Q4LNG"'); });
    await P.goto(BASE + page);
    ok(await until(() => P.evaluate(() => !!window.KPCHuntX && !!window.KPCHunt && !!document.getElementById('hxGear')), 8000), 'loads: ⚙ on the dock, ▶ SCAN, the class filter');
    await sleep(1500); await P.evaluate(async () => { if (KPCCat.connected()) await KPCCat.disconnect(); }); await sleep(800);   /* the page reconnects a remembered radio by itself: start from none */
    let r = await P.evaluate(() => ({ cls: !!document.getElementById('hxCls'), scan: !!document.getElementById('hxScan') && !!document.getElementById('hxScan').closest('.hl-viewbar') && !document.querySelector('#hlRtabs #hxScan'), vk: (document.querySelector('.dk-top [data-vk-open]') || {}).hidden, cwb: document.getElementById('hxCwB').hidden,
      ids: ['dFreq', 'dMode', 'dBand', 'dRef', 'dName', 'dCall', 'dRs', 'dRr', 'dSt', 'dNote', 'dkClr', 'dkLog', 'dkRad'].every(id => !!document.getElementById(id)) }));
    ok(r.cls && r.scan && r.ids, 'every original dock field is still there, plus the new parts');
    ok(r.vk === true && r.cwb === true, 'no radio: 🎙 voice keyer and 📟 CW buttons hidden');
    /* class filter */
    r = await P.evaluate(() => ({ g40: KPCHuntX.allowed(7150, 'G', 'SSB'), e40: KPCHuntX.allowed(7150, 'E', 'SSB'), g20: KPCHuntX.allowed(14250, 'G', 'USB'), g20e: KPCHuntX.allowed(14160, 'G', 'SSB'), gcw: KPCHuntX.allowed(14010, 'G', 'CW'), tcw: KPCHuntX.allowed(7030, 'T', 'CW'), tph: KPCHuntX.allowed(7200, 'T', 'SSB') }));
    ok(!r.g40 && r.e40 && r.g20 && !r.g20e && !r.gcw && r.tcw && !r.tph, 'band plan: General not on 7.150 / 14.160 SSB or 14.010 CW; Extra yes; Tech CW on 40 only');
    r = await P.evaluate(() => { document.querySelector('[data-hxcls="G"]').click(); const st = JSON.parse(localStorage.getItem('kpcHuntCls')); return { st, on: document.getElementById('hxClsOn').getAttribute('aria-pressed'), pass: KPCHuntX.pass({ khz: 14160, mode: 'SSB' }), pass2: KPCHuntX.pass({ khz: 14250, mode: 'SSB' }) }; });
    ok(r.st.cls === 'G' && r.st.on && r.on === 'true' && !r.pass && r.pass2, 'picking GENERAL turns 📜 IN MY CLASS ONLY on (remembered): 14.160 SSB hidden, 14.250 shown');
    await P.evaluate(() => { document.getElementById('hxClsOn').click(); });
    r = await P.evaluate(() => JSON.parse(localStorage.getItem('kpcHuntCls')).on); ok(r === false, 'and off again');
    /* multi-call split */
    r = await P.evaluate(() => [KPCHunt.splitCalls('KZ4CP,N4KPC').join('|'), KPCHunt.splitCalls('KZ4CP N4KPC').join('|'), KPCHunt.splitCalls('kz4cp, n4kpc;W1AW').join('|')]);
    ok(r[0] === 'KZ4CP|N4KPC' && r[1] === 'KZ4CP|N4KPC' && r[2] === 'KZ4CP|N4KPC|W1AW', 'calls split on comma, space or semicolon: ' + r.join(' / '));
    /* QRZ: one at a time */
    r = await P.evaluate(async () => { const sent = []; let live = 0, maxLive = 0; window.KPCQrz = window.KPCQrz || {}; const o = KPCQrz.send;
      KPCQrz.send = async a => { live++; maxLive = Math.max(maxLive, live); await new Promise(z => setTimeout(z, 200)); live--; sent.push((/<CALL:\d+>([^ <]+)/i.exec(a) || [])[1] || a.slice(0, 20)); return { ok: true, sure: true }; };
      await Promise.all([KPCHunt.qzOne('<CALL:5>KZ4CP <EOR>'), KPCHunt.qzOne('<CALL:5>N4KPC <EOR>')]); KPCQrz.send = o; return { sent, maxLive }; });
    ok(r.sent.join() === 'KZ4CP,N4KPC' && r.maxLive === 1, 'QRZ uploads go one at a time (both calls sent): ' + r.sent.join(', '));
    /* the radio window with no radio */
    await P.evaluate(() => document.getElementById('hxGear').click());
    ok(await until(() => P.evaluate(() => !document.getElementById('hxPop').hidden), 2000), '⚙ opens the radio window');
    for (const [t, want] of [['radio', 'CONNECT'], ['meters', 'OPEN THE METERS'], ['band', 'Connect the radio first'], ['audio', 'HOLD TO TALK'], ['more', 'Connect the radio first'], ['cw', 'Connect the radio first']]) {
      r = await P.evaluate(t => { KPCHuntX.show(t); return { txt: document.getElementById('hxBody').textContent, on: document.querySelector(`[data-hxt="${t}"]`).classList.contains('on') }; }, t);
      ok(r.on && r.txt.includes(want), 'no radio, tab ' + t + ': "' + want + '"');
    }
    r = await P.evaluate(() => { const p = document.getElementById('hxPop').getBoundingClientRect(); return { w: Math.round(p.width), saved: JSON.parse(localStorage.getItem('kpcHuntPop')).tab }; });
    ok(r.w <= 440 && r.saved === 'cw', 'small window (' + r.w + ' px wide), remembers the last tab');
    /* connect the pretend radio from the Radio tab */
    await P.evaluate(() => KPCHuntX.show('radio')); await P.evaluate(() => document.getElementById('hxConn').click());
    ok(await until(() => P.evaluate(() => KPCCat.connected()), 6000), '🔌 CONNECT in the window connects the radio');
    await sleep(800);
    r = await P.evaluate(() => ({ vk: document.querySelector('.dk-top [data-vk-open]').hidden, cwb: document.getElementById('hxCwB').hidden, st: document.getElementById('hxSt').textContent }));
    ok(r.vk === false && r.cwb === false && /IC-7300/.test(r.st), 'connected: 🎙 and 📟 show on the dock; the window says IC-7300');
    r = await P.evaluate(async () => { KPCHuntX.show('more'); await new Promise(z => setTimeout(z, 300)); const box = document.getElementById('lrBox'); return { inPop: !!box && box.closest('#hxPop') != null, more: !!document.getElementById('lrMore') && getComputedStyle(document.getElementById('lrMore')).display !== 'none', band: document.getElementById('lrBand') && getComputedStyle(document.getElementById('lrBand')).display }; });
    ok(r.inPop && r.more && r.band === 'none', '🎛 More: the radio box is in the window, showing only MORE / scope / guide');
    r = await P.evaluate(async () => { __rig.wrote.length = 0; document.querySelector('#hxPop [data-xt="split"]').click(); await new Promise(z => setTimeout(z, 400)); return __rig.wrote.join(' | '); });
    ok(/fe fe 94 e0 0f 01 fd/.test(r), 'SPLIT from the window reaches the radio (0F 01)');
    r = await P.evaluate(async () => { KPCHuntX.show('band'); await new Promise(z => setTimeout(z, 200)); return { band: getComputedStyle(document.getElementById('lrBand')).display, more: getComputedStyle(document.getElementById('lrMore')).display, tune: !!document.getElementById('lrTune') }; });
    ok(r.band !== 'none' && r.more === 'none' && r.tune, '📍 Bands · Tune · SWR tab shows the band buttons + 🔧 TUNE');
    /* audio / talk: keys at once */
    r = await P.evaluate(async () => { KPCHuntX.show('audio'); await new Promise(z => setTimeout(z, 300)); const c = [...document.querySelectorAll('[data-hxv]')].map(b => b.textContent);
      document.querySelector('[data-hxv="contest"]').click(); __rig.wrote.length = 0; const t0 = performance.now();
      document.getElementById('hxTalk').dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, pointerId: 1 })); await new Promise(z => setTimeout(z, 250));
      const keyed = __rig.wrote.some(w => /fe fe 94 e0 1c 00 01 fd/.test(w)); await new Promise(z => setTimeout(z, 600));
      document.getElementById('hxTalk').dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 })); await new Promise(z => setTimeout(z, 600));
      return { c, keyed, unkey: __rig.wrote.some(w => /fe fe 94 e0 1c 00 00 fd/.test(w)), voice: JSON.parse(localStorage.getItem('kpcHuntTalk')).voice, hear: getComputedStyle(document.getElementById('lrHear')).display, pw: !document.getElementById('hxPw').closest('.hx-row').hidden, mg: !document.getElementById('hxMg').closest('.hx-row').hidden }; });
    ok(r.c.join() === 'NATURAL,PUNCH,CONTEST' && r.voice === 'contest', '🎧 Audio · Mic: NATURAL / PUNCH / CONTEST (CONTEST remembered)');
    ok(r.keyed && r.unkey, '🎙 HOLD TO TALK keys the radio within 250 ms of the press and lets go on release');
    ok(r.hear !== 'none' && r.pw && r.mg, 'hear-the-radio (noise clean-up) + RF POWER + RADIO MIC GAIN there for an IC-7300');
    r = await P.evaluate(async () => { __rig.wrote.length = 0; const s = document.getElementById('hxPw'); s.value = '40'; s.dispatchEvent(new Event('change')); for (let i = 0; i < 30 && !__rig.wrote.some(w => / 14 0a /.test(w)); i++) await new Promise(z => setTimeout(z, 100)); return __rig.wrote.join(' | '); });
    ok(/fe fe 94 e0 14 0a 01 02 fd/.test(r), 'RF POWER 40 % → 14 0A 0102 to the radio');
    /* CW */
    r = await P.evaluate(async () => { document.getElementById('dCall').value = 'W1AW'; KPCHuntX.show('cw'); await new Promise(z => setTimeout(z, 200)); __rig.wrote.length = 0;
      document.querySelector('[data-cwm="1"]').click(); for (let i = 0; i < 30 && !__rig.wrote.some(w => / 17 /.test(w)); i++) await new Promise(z => setTimeout(z, 100)); await new Promise(z => setTimeout(z, 200)); document.getElementById('dCall').value = '';
      const h = __rig.wrote.join(' | '); const txt = h.split(' | ').filter(w => / 17 /.test(w)).map(w => w.split(' ').slice(5, -1).map(x => String.fromCharCode(parseInt(x, 16))).join('')).join('');
      return { mem: document.querySelectorAll('[data-cwm]').length, txt }; });
    ok(r.mem === 6 && r.txt === 'W1AW TU 5NN KY', '📟 CW: 6 memories; M2 sends "' + r.txt + '" through the radio\'s keyer (CI-V 17)');
    /* scan */
    r = await P.evaluate(async () => { window.KPCHuntShown = [{ p: 'POTA', call: 'K1AAA', ref: 'US-0001', khz: 14250, mode: 'SSB' }, { p: 'POTA', call: 'K2BBB', ref: 'US-0002', khz: 7074, mode: 'FT8' }, { p: 'POTA', call: 'K3CCC', ref: 'US-0003', khz: 7200, mode: 'SSB' }];
      KPCHuntX.scStart(); await new Promise(z => setTimeout(z, 600)); const a = (await KPCCat.read()).khz; const btn = document.getElementById('hxScan').textContent; const call1 = document.getElementById('dCall').value;
      KPCHuntX.scStop(); return { a, btn, call1, after: document.getElementById('hxScan').textContent }; });
    ok(r.a === 14250 && /STOP/.test(r.btn) && r.call1 === 'K1AAA' && /SCAN/.test(r.after), '▶ SCAN tunes the first voice spot (FT8 skipped), fills the dock; ⏹ stops it');
    /* close: the public lounge gets its radio box back */
    await P.evaluate(() => KPCHuntX.close());
    r = await P.evaluate(() => { const box = document.getElementById('lrBox'); return { home: !!document.getElementById('ctCat'), back: box ? !!box.closest('#ctCat') : null, gone: !box || !box.isConnected }; });
    ok(r.home ? r.back : r.gone, r.home ? 'closing gives the RADIO CONTROL card its box back' : 'closing puts the radio box away (no card on this page)');
    r = await P.evaluate(() => document.documentElement.scrollWidth - innerWidth); ok(r <= 1, 'no sideways scroll');
    await P.setViewportSize({ width: 390, height: 844 }); await P.evaluate(() => KPCHuntX.open('audio')); await sleep(300);
    r = await P.evaluate(() => { const p = document.getElementById('hxPop').getBoundingClientRect(); return { l: Math.round(p.left), r: Math.round(innerWidth - p.right), sx: document.documentElement.scrollWidth - innerWidth }; });
    ok(r.l >= 0 && r.r >= 0 && r.sx <= 1, 'phone width: the window fits the screen');
    await P.screenshot({ path: '/tmp/hx-' + page.replace('.html', '') + '-phone.png' });
    await P.setViewportSize({ width: 1280, height: 900 }); await P.evaluate(() => KPCHuntX.show('more')); await sleep(300); await P.screenshot({ path: '/tmp/hx-' + page.replace('.html', '') + '.png' });
    ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 6).join(' | ') : ''));
    await ctx.close();
  }
  await b.close(); console.log(fails ? '\n' + fails + ' FAILED' : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
