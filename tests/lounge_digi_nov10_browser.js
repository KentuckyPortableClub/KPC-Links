/* Browser check for the Nov 10 FT8-tab round (the KPC app's FT8 screen fixes ported into kpc-logger-ft8.js), on kpc-hunt.html (VIP), kpc-hunters.html
   and kpc-logger.html?old=1. Fake microphone (a beep) for level + watchdog; a real FT8 signal (made with KPCFT8's own encoder) for the highlights.
   Not part of kpc_full_suite.py (needs Chromium + Playwright). Run:
     python3 -m http.server 8795 &   BASE=http://127.0.0.1:8795/ NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules node tests/lounge_digi_nov10_browser.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8795/';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { try { if (await fn()) return true; } catch (e) {} await sleep(100); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic|geolocation|Geolocation/i;
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
const ARGS = ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required'];
async function mk(b, vp, grid, extra) {
  const ctx = await b.newContext({ viewport: vp || { width: 1280, height: 900 }, permissions: ['microphone'] });
  await ctx.route(/api\.pota\.app|sota|spothole/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
  await ctx.addInitScript(([vip, grid]) => { localStorage.setItem('kpcVipOK', vip); localStorage.setItem('kpcMyCall', '"K4TEST"'); localStorage.setItem('kpcHuntQSO', JSON.stringify({ v: 1, u: 0, grid, q: [] })); localStorage.setItem('kpcLgSet', JSON.stringify({ call: 'K4TEST', grid })); if (!sessionStorage.__ft8init) { sessionStorage.__ft8init = 1; localStorage.removeItem('kpcFt8'); localStorage.removeItem('kpcFt8Open:' + location.pathname); } }, [VIP, grid]);
  if (extra) await ctx.addInitScript(extra);
  const P = await ctx.newPage(); P.errs = [];
  P.on('pageerror', e => { if (!NET.test(e.message)) P.errs.push('PE ' + e.message); }); P.on('console', m => { if (m.type() === 'error' && !NET.test(m.text())) P.errs.push(m.text()); });
  P.on('dialog', d => d.accept());
  return P;
}
const openTab = async P => { await P.evaluate(() => { const b = [...document.querySelectorAll('.rt-f8,[data-ft8open]')].find(x => x.offsetParent !== null) || document.querySelector('[data-ft8open]'); b.click(); }); return until(() => P.evaluate(() => !document.getElementById('cFt8').hidden), 4000); };
const txt = (P, id) => P.evaluate(i => (document.getElementById(i) || {}).textContent || '', id);
const IDS = ['f8LvlBar', 'f8LvlW', 'f8TopLvl', 'f8Qso', 'f8QsoDx', 'f8QsoR', 'f8QsoL', 'f8QsoClr', 'f8Clear', 'f8AutoClr', 'f8WfB', 'f8WfC', 'f8WfBT', 'f8WfCT', 'f8hl_park', 'f8hl_dxped', 'f8hl_event', 'f8hl_dx', 'f8hl_newc', 'f8hl_newb', 'f8Txm', 'f8Rx', 'f8Band1'];

/* kpc-hunters.html is the public lounge: the digi modes are VIP-only, the FT8 tab stays hidden there and nothing from the new code shows */
async function pub(b) {
  console.log('== kpc-hunters.html (public: FT8 tab must stay hidden)');
  const P = await mk(b, null, ''); await P.goto(BASE + 'kpc-hunters.html'); await sleep(2500);
  const r = await P.evaluate(() => { const vis = e => !!(e && e.offsetParent !== null && getComputedStyle(e).visibility !== 'hidden'); const bs = [...document.querySelectorAll('.rt-f8,[data-ft8open]')];
    return { btns: bs.length, shown: bs.filter(vis).length, root: vis(document.getElementById('cFt8')), lvl: vis(document.getElementById('f8TopLvl')), qso: vis(document.getElementById('f8Qso')), clr: vis(document.getElementById('f8Clear')), hasJs: !![...document.scripts].find(s => /kpc-logger-ft8\.js\?v=20261020d/.test(s.src)) }; });
  ok(r.shown === 0 && !r.root && !r.lvl && !r.qso && !r.clr, 'FT8 tab button(s) hidden (' + r.btns + ' in page, ' + r.shown + ' visible); level word, QSO box, CLEAR SPOT not visible');
  ok(r.hasJs, 'the page still loads the old script version (untouched)');
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : '')); await P.context().close();
}
async function body(b, page, url) {
  console.log('== ' + page + (url.includes('?') ? '?' + url.split('?')[1] : ''));
  const P = await mk(b, null, '');
  await P.goto(BASE + url);
  ok(await until(() => P.evaluate(() => !!window.KPCFt8Tab && !!document.getElementById('cFt8')), 8000), 'FT8 tab script loaded (window.KPCFt8Tab)');
  await sleep(800);
  ok(await openTab(P), 'the FT8 tab opens from its button');
  ok(await P.evaluate(ids => ids.every(i => !!document.getElementById(i)), IDS), 'all the new ids exist');
  ok(await P.evaluate(() => ['f8Txm', 'f8Rx', 'f8Band1', 'f8PotaF', 'f8Cq', 'f8En', 'f8Halt', 'f8Tune', 'f8Gen', 'f8NoG', 'f8Lvl'].every(i => !!document.getElementById(i))), 'old parts still there (TX1-6, RX FREQUENCY list, CQ, ENABLE TX, ⚡ Fast QSO, ⚙ level)');
  /* settings defaults */
  let r = await P.evaluate(() => ({ ac: document.getElementById('f8AutoClr').checked, hl: ['park', 'dxped', 'event', 'dx', 'newc', 'newb'].map(k => document.getElementById('f8hl_' + k).checked).join('') }));
  ok(r.ac && r.hl === 'truetruetruefalsefalsefalse'.replace(/true/g, '1').replace(/false/g, '0') || (r.ac && r.hl === 'truetruetruefalsefalsefalse'), 'defaults: auto clear spot ON; highlights park / DXpedition / event ON, DX / never-worked / other-band OFF (' + r.hl + ')');
  /* NO GRID */
  await P.evaluate(() => { document.getElementById('f8En').click(); }); await until(() => P.evaluate(() => /Put your grid/.test(document.getElementById('f8Note').textContent)), 6000);
  r = await P.evaluate(() => ({ n: document.getElementById('f8Note').textContent, hid: document.getElementById('f8Note').hidden, tx: KPCFt8Tab.txOn() }));
  ok(/Put your grid in .* first: the CQ and the first call carry it/.test(r.n) && !r.hid && !r.tx, 'no grid: ENABLE TX refused with the note: "' + r.n + '"');
  ok(await until(() => P.evaluate(() => KPCFt8Tab.running()), 6000), 'START LISTENING happened (ENABLE TX starts the sound, then refuses)');
  await P.evaluate(() => document.getElementById('f8Cq').click()); await sleep(300);
  r = await P.evaluate(() => ({ n: document.getElementById('f8Note').textContent, tx: KPCFt8Tab.txOn() }));
  ok(/Put your grid/.test(r.n) && !r.tx, 'no grid: CQ refused too');
  r = await P.evaluate(() => { const T = KPCFt8Tab; T.S.noGrid = true; document.getElementById('f8NoG').checked = true; document.getElementById('f8NoG').dispatchEvent(new Event('change')); const sl = Math.floor(Date.now() / 15000); T._feed(sl, [{ text: 'CQ Q4AAA EM77', hz: 900 }]); const id = T.ids().pop(); T.pick(+id); const a = T.txOn(); T.S.noGrid = false; document.getElementById('f8NoG').checked = false; document.getElementById('f8NoG').dispatchEvent(new Event('change')); return { a }; });
  ok(r.a === true, '⚡ Fast QSO with no grid: answering a station (reports only) still switches TX on');
  await P.evaluate(() => { document.getElementById('f8Halt').click(); const q = KPCFt8Tab.qso(); q.dx = ''; q.state = 'idle'; document.getElementById('f8Dx').value = ''; document.getElementById('f8Dx').onchange(); });
  /* RX level bar + word */
  ok(await until(() => P.evaluate(() => KPCFt8Tab.lvl().w !== '--'), 6000), 'RX level word shows in the top strip');
  r = await P.evaluate(() => ({ l: KPCFt8Tab.lvl(), w: parseFloat(document.getElementById('f8LvlBar').style.width) || 0, vis: !!document.getElementById('f8TopLvl').offsetParent }));
  ok(['too quiet', 'good', 'loud', 'TOO LOUD'].includes(r.l.w) && r.vis, 'word is one of too quiet / good / loud / TOO LOUD: "' + r.l.w + '" at ' + r.l.db + ' dB, bar ' + Math.round(r.w) + '%');
  r = await P.evaluate(() => { const T = KPCFt8Tab; const z = d => { const p = document.getElementById('f8TopLvl'); return p; }; return true; });
  /* QSO box */
  r = await P.evaluate(() => ({ dx: document.getElementById('f8QsoDx').textContent, clr: !!document.getElementById('f8QsoClr').offsetParent, below: document.getElementById('f8Qso').getBoundingClientRect().top >= document.getElementById('f8Txm').getBoundingClientRect().bottom - 2 }));
  ok(r.dx === 'NO CONTACT' && r.clr && r.below, 'QSO box under TX1-6 with a CLEAR button; idle header: ' + r.dx);
  r = await P.evaluate(() => { const T = KPCFt8Tab, sl = Math.floor(Date.now() / 15000); T._feed(sl, [{ text: 'K4TEST Q4CCC EM77', hz: 1700 }, { text: 'CQ Q4DDD EM77', hz: 2300 }]); const ids = T.ids(); const x = T.lines().find(l => l.fr === 'Q4CCC'); T.pick(x.id);
    return { dx: document.getElementById('f8QsoDx').textContent, rr: document.getElementById('f8QsoR').textContent, rows: document.querySelectorAll('#f8QsoL > div').length, miss: !!document.querySelector('#f8QsoR .miss') }; });
  ok(/Q4CCC/.test(r.dx) && /SENT/.test(r.rr) && /missing report/.test(r.rr) && r.rows >= 1, 'QSO box: header "' + r.dx + '" / "' + r.rr + '", ' + r.rows + ' line(s)');
  r = await P.evaluate(() => { document.getElementById('f8QsoClr').click(); const T = KPCFt8Tab; return { dx: document.getElementById('f8QsoDx').textContent, q: T.qso().dx, rows: document.querySelectorAll('#f8QsoL > div').length }; });
  ok(r.dx === 'NO CONTACT' && r.q === '' && r.rows === 0, 'CLEAR empties the box and (not transmitting) clears the contact' + JSON.stringify(r));
  /* CLEAR SPOT */
  await sleep(1200);
  r = await P.evaluate(() => { const T = KPCFt8Tab, sl = Math.floor(Date.now() / 15000); T.S.txHz = 1500; document.getElementById('f8TxHz').value = 1500; T.S.autoClear = false;
    T._feed(sl, [{ text: 'CQ Q4EEE EM77', hz: 1480 }, { text: 'CQ Q4FFF EM77', hz: 1530 }, { text: 'CQ Q4GGG EM77', hz: 1000 }]); T.S.autoClear = true; T.S.txHz = 1500; document.getElementById('f8Clear').click();
    const hz = T.S.txHz, near = T.lines().filter(l => l.hz && Math.abs(l.hz - hz) < 50).length; return { hz, box: document.getElementById('f8TxHz').value, near }; });
  ok(r.hz !== 1500 && r.hz >= 300 && r.hz <= 2700 && r.near === 0 && +r.box === r.hz, 'CLEAR SPOT moved TX from 1500 to ' + r.hz + ' Hz (no decoded signal within 50 Hz), TX Hz box follows');
  r = await P.evaluate(() => { const T = KPCFt8Tab; T.S.txHz = 1200; const a = T._autoTest(1200); T.qso().dx = 'Q4CCC'; T.qso().state = 'call'; T.S.txHz = 1200; const b = T._autoTest(1200); T.qso().dx = ''; T.qso().state = 'idle'; T.S.autoClear = false; T.S.txHz = 1200; const c = T._autoTest(1200); T.S.autoClear = true; return { a, b, c }; });
  ok(r.a.moved && !r.b.moved && !r.c.moved, 'auto clear spot: moves off a taken spot (to ' + r.a.to + '), stays put with a contact in hand, stays put when switched off');
  /* waterfall sliders */
  r = await P.evaluate(() => { const set = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event('input')); }; set('f8WfB', 40); set('f8WfC', -30); const s = JSON.parse(localStorage.getItem('kpcFt8')); return { b: s.wfB, c: s.wfC, bt: document.getElementById('f8WfBT').textContent, ct: document.getElementById('f8WfCT').textContent, live: KPCFt8Tab.S.wfB }; });
  ok(r.b === 40 && r.c === -30 && r.bt === '40' && r.ct === '-30' && r.live === 40, 'brightness / contrast sliders change S live and are saved (kpcFt8: ' + r.b + ' / ' + r.c + ')');
  /* highlights (rule table) */
  r = await P.evaluate(() => { const T = KPCFt8Tab; window.KPCHuntShown = [{ call: 'Q4DXP', p: 'DXPED' }, { call: 'Q4EVT', p: 'EVENT' }]; const H = { park: 1, dxped: 1, event: 1, dx: 0, newc: 0, newb: 0 };
    const o = {}; o.park = T._hl({ fr: 'Q4AAA', cqw: 'POTA' }, H); o.x11 = T._hl({ fr: 'K4X' }); o.w1aw = T._hl({ fr: 'W1AW/4' }); o.dxped = T._hl({ fr: 'Q4DXP' }); o.evt = T._hl({ fr: 'Q4EVT' }); o.plain = T._hl({ fr: 'Q4BBB' });
    o.dx = T._hl({ fr: 'Q4BBB' }, { park: 1, dxped: 1, event: 1, dx: 1, newc: 0, newb: 0 }); o.us = T._hl({ fr: 'W4ABC' }, { park: 1, dxped: 1, event: 1, dx: 1, newc: 0, newb: 0 });
    o.newc = T._hl({ fr: 'Q4NEW' }, { park: 0, dxped: 0, event: 0, dx: 0, newc: 1, newb: 0 }); T.S.hl = H; return o; });
  ok(r.park === 'park' && r.x11 === 'event' && r.w1aw === 'event' && r.dxped === 'dxped' && r.evt === 'event' && r.plain === '' && r.dx === 'dx' && r.us === '' && r.newc === 'newc', 'highlight rules: ' + JSON.stringify(r));
  /* watchdog */
  await P.evaluate(() => { document.getElementById('f8Halt').click(); }); await sleep(500);
  r = await P.evaluate(() => KPCFt8Tab._restarts());
  await P.evaluate(() => KPCFt8Tab._wedge());
  ok(await until(() => P.evaluate(n => KPCFt8Tab._restarts() > n, r), 4000), 'watchdog: a stuck decoder (sound still arriving, no pass) gets restarted');
  ok(await until(async () => /Decoder restarted/.test(await txt(P, 'f8Note')), 3000) || (await P.evaluate(() => KPCFt8Tab._notes())).some(t => /Decoder restarted/.test(t)), 'and says "Decoder restarted"');
  ok(await until(() => P.evaluate(() => KPCFt8Tab.eng()), 8000), 'a fresh engine is loaded after the restart');
  r = await P.evaluate(() => KPCFt8Tab._restarts()); await sleep(1500); ok((await P.evaluate(() => KPCFt8Tab._restarts())) === r, 'restart happens once, not in a loop');
  await P.evaluate(() => KPCFt8Tab._quiet(7));
  ok(await until(() => P.evaluate(() => /No stations decoded for 7 slots/.test(document.getElementById('f8Note').textContent)), 3000), 'watchdog: 7 quiet slots with sound gives the hint (RX level / radio / clock)');
  await P.evaluate(() => document.querySelector('[data-f8m="CW"]').click()); await sleep(300);
  r = await P.evaluate(() => { KPCFt8Tab._wedge(); return KPCFt8Tab._restarts(); }); await sleep(1500);
  ok((await P.evaluate(() => KPCFt8Tab._restarts())) === r, 'watchdog stays quiet in CW mode');
  await P.evaluate(() => document.querySelector('[data-f8m="FT8"]').click()); await sleep(1500);
  ok((await P.evaluate(() => KPCFt8Tab._restarts())) === r, 'and does not fire when coming back to FT8');
  /* with a grid, TX is allowed (fresh page) */
  ok(P.errs.length === 0, 'no page errors' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : ''));
  await P.context().close();
  const G = await mk(b, null, 'EM77'); await G.goto(BASE + url); await until(() => G.evaluate(() => !!window.KPCFt8Tab), 8000); await sleep(800); await openTab(G);
  await G.evaluate(() => document.getElementById('f8En').click()); ok(await until(() => G.evaluate(() => KPCFt8Tab.txOn()), 6000), 'with a grid (EM77) set: ENABLE TX switches TX on');
  await G.evaluate(() => document.getElementById('f8En').click()); await G.evaluate(() => document.getElementById('f8Cq').click()); await sleep(400);
  ok(await G.evaluate(() => KPCFt8Tab.txOn() && KPCFt8Tab.qso().cq), 'and 📣 CQ works');
  await G.evaluate(() => document.getElementById('f8Halt').click());
  ok(G.errs.length === 0, 'no page errors (grid page)' + (G.errs.length ? ': ' + G.errs.slice(0, 3).join(' | ') : '')); await G.context().close();
}

/* a real FT8 signal into the page: the page's own encoder (KPCFT8.tones + synth) builds 15 s of five stations, looped on the UTC slot clock, handed over as the microphone */
const FAKE_MIC = () => {
  const MSG = [['CQ POTA Q4AAA EM77', 800], ['CQ K4X EM77', 1100], ['CQ Q4BBB EM77', 1400], ['K4TEST Q4CCC EM77', 1700], ['CQ Q4DXP EM77', 2000]];
  navigator.mediaDevices.getUserMedia = async () => {
    const e = await KPCFT8.load('kpc-ft8.wasm?v=20261017a'), AC = new AudioContext(), rate = AC.sampleRate, buf = AC.createBuffer(1, rate * 15, rate), d = buf.getChannelData(0);
    for (const [m, hz] of MSG) { const t = e.tones(m, false), au = KPCFT8.synth(t, hz, rate, false); for (let i = 0; i < au.length && i + Math.round(0.5 * rate) < d.length; i++) d[i + Math.round(0.5 * rate)] += au[i] * 0.2; }
    const src = AC.createBufferSource(); src.buffer = buf; src.loop = true; const dest = AC.createMediaStreamDestination(); src.connect(dest);
    await AC.resume(); src.start(AC.currentTime + (15 - ((Date.now() / 1000) % 15))); window.__fakeAC = AC; return dest.stream;
  };
};
async function real(b) {
  console.log('== real FT8 signal on kpc-hunt.html (waits for two decode passes)');
  const P = await mk(b, null, 'EM77', FAKE_MIC);
  await P.goto(BASE + 'kpc-hunt.html'); await until(() => P.evaluate(() => !!window.KPCFt8Tab), 8000); await sleep(800);
  await P.evaluate(() => { window.KPCHuntShown = [{ call: 'Q4DXP', p: 'DXPED' }]; });
  await openTab(P); await P.evaluate(() => document.getElementById('f8Start').click());
  ok(await until(() => P.evaluate(() => KPCFt8Tab.running()), 8000), 'START LISTENING with the made-up radio audio');
  const got = await until(() => P.evaluate(() => KPCFt8Tab.lines().filter(l => l.fr).length >= 4), 70000);
  const L = await P.evaluate(() => KPCFt8Tab.lines().filter(l => l.fr).map(l => l.text));
  ok(got, 'the page decoded the injected signal: ' + [...new Set(L)].join(' | '));
  const cls = await P.evaluate(() => { const o = {}; document.querySelectorAll('#f8Band1 .f8-l').forEach(d => { o[(d.querySelector('.m').textContent.match(/Q4\w+|K4X/) || [''])[0]] = d.className; }); return o; });
  ok(/park/.test(cls.Q4AAA || ''), '🌲 park activator row keeps its park marking: ' + cls.Q4AAA);
  ok(/hl-event/.test(cls.K4X || ''), '🎉 1x1 call K4X lights up as a special event');
  ok(/hl-dxped/.test(cls.Q4DXP || ''), '🏝 DXpedition from the Lounge spot list lights up');
  ok(!/hl-dx\b/.test(cls.Q4BBB || '') && !/hl-newc/.test(cls.Q4BBB || ''), 'DX / never-worked are off by default');
  await P.evaluate(() => { for (const k of ['dx', 'newc']) document.getElementById('f8hl_' + k).click(); }); await sleep(300);
  const c2 = await P.evaluate(() => { const o = {}; document.querySelectorAll('#f8Band1 .f8-l').forEach(d => { o[(d.querySelector('.m').textContent.match(/Q4\w+|K4X/) || [''])[0]] = d.className + '|' + d.querySelector('.m').textContent; }); return o; });
  ok(/hl-dx\b/.test(c2.Q4BBB || '') && /🌍/.test(c2.Q4BBB || ''), '🌍 DX checkbox on: Q4BBB lights up with 🌍 (my call K4TEST is US)');
  const sv = await P.evaluate(() => JSON.parse(localStorage.getItem('kpcFt8')).hl); ok(sv.dx === 1 && sv.newc === 1, 'highlight choices are saved: ' + JSON.stringify(sv));
  await P.evaluate(() => { for (const k of ['dx', 'newc']) document.getElementById('f8hl_' + k).click(); });
  /* tap = light every line of that station */
  await P.evaluate(() => { document.getElementById('f8Halt').click(); const rows = [...document.querySelectorAll('#f8Band1 .f8-l')].filter(d => /Q4CCC/.test(d.textContent)); rows[rows.length - 1].click(); }); await sleep(400);
  const ds = await P.evaluate(() => ({ band: document.querySelectorAll('#f8Band1 .dxsel').length, rx: document.querySelectorAll('#f8Rx .dxsel').length, qso: document.getElementById('f8QsoDx').textContent, rows: document.querySelectorAll('#f8QsoL > div').length, other: [...document.querySelectorAll('#f8Band1 .dxsel')].every(d => /Q4CCC/.test(d.textContent)) }));
  ok(ds.band >= 1 && ds.rx >= 1 && ds.other, 'tapping a decode lights its lines in BOTH lists (.dxsel: ' + ds.band + ' + ' + ds.rx + ')');
  ok(/Q4CCC/.test(ds.qso) && ds.rows >= 1, 'and the QSO box shows the contact: ' + ds.qso + ', ' + ds.rows + ' line(s)');
  await P.evaluate(() => document.getElementById('f8Halt').click());
  /* screenshots */
  await P.evaluate(() => { document.getElementById('f8QsoClr').click(); const T = KPCFt8Tab; const rows = [...document.querySelectorAll('#f8Band1 .f8-l')].filter(d => /Q4CCC/.test(d.textContent)); rows[rows.length - 1].click(); document.getElementById('f8Halt').click(); });
  await P.setViewportSize({ width: 1280, height: 900 }); await sleep(500); await P.screenshot({ path: '/tmp/digi-desk.png' });
  await P.evaluate(() => { const f = document.getElementById('cFt8'); f.scrollTop = 520; }); await sleep(200); await P.screenshot({ path: '/tmp/digi-desk2.png' });
  await P.evaluate(() => { document.getElementById('f8Set').open = true; const f = document.getElementById('cFt8'); f.scrollTop = 99999; }); await sleep(200); await P.screenshot({ path: '/tmp/digi-desk3.png' });
  const ov = d => P.evaluate(() => { const f = document.getElementById('cFt8'); return { sw: f.scrollWidth, cw: f.clientWidth, bad: [...f.querySelectorAll('*')].filter(e => { const r = e.getBoundingClientRect(); return e.offsetParent && !e.closest('#f8BandR,.f8-modes') && r.width && (r.right > innerWidth + 2); }).slice(0, 5).map(e => (e.id || e.className || e.tagName) + ':' + Math.round(e.getBoundingClientRect().right)) }; });
  let o = await ov(); ok(o.sw <= o.cw + 1 && !o.bad.length, 'desktop: nothing runs off the side ' + JSON.stringify(o));
  await P.setViewportSize({ width: 390, height: 844 }); await sleep(600);
  await P.evaluate(() => { document.getElementById('f8Set').open = false; document.getElementById('cFt8').scrollTop = 0; }); await sleep(300); await P.screenshot({ path: '/tmp/digi-phone.png' });
  await P.evaluate(() => { document.getElementById('cFt8').scrollTop = 700; }); await sleep(200); await P.screenshot({ path: '/tmp/digi-phone2.png' });
  await P.evaluate(() => { document.getElementById('f8Set').open = true; document.getElementById('cFt8').scrollTop = 99999; }); await sleep(200); await P.screenshot({ path: '/tmp/digi-phone3.png' });
  o = await ov(); ok(o.sw <= o.cw + 1 && !o.bad.length, 'phone: nothing runs off the side ' + JSON.stringify(o));
  ok(P.errs.length === 0, 'no page errors (real-signal page)' + (P.errs.length ? ': ' + P.errs.slice(0, 3).join(' | ') : ''));
  await P.context().close();
}
(async () => {
  const b = await chromium.launch({ args: ARGS });
  for (const [pg, url] of [['kpc-hunt.html', 'kpc-hunt.html'], ['kpc-logger.html', 'kpc-logger.html?old=1']]) await body(b, pg, url);
  await pub(b); await real(b);
  await b.close(); console.log(`\n${fails ? 'FAILED' : 'ALL PASSED'}: ${passes} passed, ${fails} failed`); process.exit(fails ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
