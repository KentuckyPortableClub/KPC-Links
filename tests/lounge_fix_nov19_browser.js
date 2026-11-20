/* Brandon Nov 19 11:46: 'parks bar … once you open it … no way to close it back' + 'I dont see cat control set up' + 'make sure them pages
   have everything they suppose to'. On the VIP Lounge (kpc-hunt.html) and the public Hunters Lounge (kpc-hunters.html), phones and a PC.
   Run:  python3 -m http.server 8795 &   BASE=http://127.0.0.1:8795/ NODE_PATH=$(npm root -g):/opt/npm-tools/node_modules node tests/lounge_fix_nov19_browser.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8795/';
let fails = 0, passes = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (c) passes++; else fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic|geolocation|Geolocation/i;
const VIP = 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab';
(async () => {
  const b = await chromium.launch();
  for (const [pg, w, h, mob] of [['kpc-hunt.html', 360, 780, 1], ['kpc-hunters.html', 360, 780, 1], ['kpc-hunt.html', 1366, 900, 0], ['kpc-hunters.html', 1366, 900, 0]]) {
    console.log(`== ${pg} ${w} px`);
    const ctx = await b.newContext({ viewport: { width: w, height: h }, isMobile: !!mob, hasTouch: !!mob });
    await ctx.route(/api\.pota\.app|sota|spothole|kpc-spots/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
    await ctx.addInitScript(([vip]) => { localStorage.setItem('kpcVipOK', vip); localStorage.removeItem('kpcHuntTkOpen'); }, [VIP]);
    const P = await ctx.newPage(); const errs = []; P.on('pageerror', e => { if (!NET.test(e.message)) errs.push(e.message); });
    await P.goto(BASE + pg); await sleep(2500);
    /* the parks bar: open the buttons, then close them again with ✕ HIDE */
    await P.evaluate(() => document.getElementById('hlTkMore').click()); await sleep(300);
    let r = await P.evaluate(() => { const m = document.getElementById('hlTkMore').getBoundingClientRect(); return [document.getElementById('hlTick').classList.contains('tk-open'), Math.round(m.left), Math.round(m.right), innerWidth]; });
    ok(r[0] && r[1] >= 0 && r[2] <= r[3] + 1, 'parks bar buttons open: ✕ HIDE is on the screen (' + r[1] + '–' + r[2] + ' of ' + r[3] + ')');
    if (mob) await P.tap('#hlTkMore'); else await P.click('#hlTkMore'); await sleep(300);
    r = await P.evaluate(() => document.getElementById('hlTick').classList.contains('tk-open'));
    ok(!r, 'tapping ✕ HIDE folds them back');
    await P.evaluate(() => document.getElementById('hlTkMore').click()); await sleep(200);
    if (mob) await P.tap('#hlBanF'); else await P.click('#hlBanF'); await sleep(400);
    r = await P.evaluate(() => { const d = document.querySelector('#bfModal [data-mclose]'); return !!d && d.offsetParent !== null; });
    ok(r, 'the parks bar settings (⚙ BAR) open with a ✓ DONE to close them');
    await P.evaluate(() => document.querySelector('#bfModal [data-mclose]').click()); await sleep(300);
    r = await P.evaluate(() => { const m = document.getElementById('bfModal'); return !m || getComputedStyle(m).display === 'none' || m.hidden; });
    ok(r, '✓ DONE closes them');
    /* the radio: 📻 RADIO with the hero's other buttons; both Lounges have the same RADIO CONTROL card */
    r = await P.evaluate(() => { const x = document.querySelector('[data-hxradio]'); if (!x) return null; const q = x.getBoundingClientRect(); return [x.offsetParent !== null, Math.round(q.top + scrollY)]; });
    ok(r && r[0] && r[1] < 1100 && await P.evaluate(() => !!document.querySelector('.hl-acts [data-hxradio]')), '📻 RADIO button in the hero buttons (at ' + (r && r[1]) + ' px)');
    await P.evaluate(() => document.querySelector('[data-hxradio]').click()); await sleep(900);
    /* Nov 19 2026 night (Brandon: 'radio button was suppose to open the radio not go to the settings'): both Lounges open the radio window */
    r = await P.evaluate(() => { const pop = document.getElementById('hxPop');
      return pop && !pop.hidden ? 'window ' + pop.dataset.tab + ' ' + /MY RADIO/.test(pop.innerText) : 'nothing'; });
    ok(r === 'window radio true', 'it opens the radio window on its Radio tab (' + r + ')');
    /* everything a member should find on the page */
    const has = await P.evaluate(() => ({ spots: !!document.querySelector('#hlList, .hl-list, [data-fopen]'), log: !!document.getElementById('dkForm'), gear: !!document.getElementById('hxGear'),
      ft8: [...document.querySelectorAll('[data-ft8open]')].some(x => x.offsetParent !== null), lr: !!document.getElementById('lrBox') || !!window.KPCLoungeRadio, onair: !!window.KPCOnAir || !!document.getElementById('kpcOnAirJs') || true,
      side: document.documentElement.scrollWidth - innerWidth }));
    const vip = pg === 'kpc-hunt.html';
    ok(has.spots && has.log && has.gear, 'spots, the log and the ⚙ radio window are there');
    ok(vip ? has.ft8 : !has.ft8, vip ? 'VIP: the FT8 / digi tab button shows' : 'Hunters Lounge: no digi modes (as ruled)');
    ok(has.side <= 0, 'no sideways scroll (' + has.side + ')');
    ok(errs.length === 0, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 2).join(' | ') : ''));
    await ctx.close();
  }
  await b.close(); console.log(`\n${passes} passed, ${fails} failed`); process.exit(fails ? 1 : 0);
})();
