/* Browser check (Nov 10): the VIP award badges on the spots still work after the logger round.
   🔁 Repeat Offender (park count / next 20), 🤝 Op to Op (activator count / next 50), 📶 N1CC new band (bands / 10),
   ALMOST + flash when close, tap = the badge legend, and the public lounge shows none of them.
   Not part of kpc_full_suite.py (needs Chromium + Playwright). Run:
     python3 -m http.server 8799 &   NODE_PATH=$(npm root -g) node tests/lounge_badges_nov10_browser.js */
const { chromium } = require('playwright');
const BASE = process.env.BASE || 'http://127.0.0.1:8799/';
const SHOT = process.env.SHOT || '';
let fails = 0; const ok = (c, m) => { console.log((c ? '  ✓ ' : '  ✗ ') + m); if (!c) fails++; };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const until = async (fn, ms) => { const t = Date.now(); while (Date.now() - t < (ms || 5000)) { if (await fn()) return true; await sleep(150); } return false; };
const NET = /Failed to load resource|ERR_|net::|CORS|fetch|unpkg|leaflet|L is not defined|tile|googleapis|gstatic/i;
const now = new Date().toISOString().replace('Z', '');
const SPOTS = [
  { activator: 'Q4AAA', frequency: '14250', mode: 'SSB', reference: 'US-1001', name: 'Almost Park', locationDesc: 'US-KY', grid6: 'EM78aa', spotTime: now, spotter: 'Q4SP', comments: '' },
  { activator: 'Q4BBB', frequency: '7200', mode: 'SSB', reference: 'US-1002', name: 'Far Park', locationDesc: 'US-TN', grid6: 'EM66aa', spotTime: now, spotter: 'Q4SP', comments: '' },
  { activator: 'Q4CCC', frequency: '18130', mode: 'SSB', reference: 'US-1003', name: 'Band Park', locationDesc: 'US-OH', grid6: 'EM79aa', spotTime: now, spotter: 'Q4SP', comments: '' },
  { activator: 'Q4DDD', frequency: '21300', mode: 'SSB', reference: 'US-1004', name: 'Fresh Park', locationDesc: 'US-IN', grid6: 'EM69aa', spotTime: now, spotter: 'Q4SP', comments: '' }
];
const COUNTS = { t: Date.now(),
  pc: { 'US-1001': 17, 'US-1002': 3, 'US-1003': 41 },          /* 17/20 = ALMOST; 3/20 no; 41/60 no */
  ac: { Q4AAA: 4, Q4BBB: 47, Q4CCC: 120 },                       /* 4/50 no; 47/50 ALMOST; 120/150 no */
  n1: { 'US-1001': '20M', 'US-1003': '20M,40M,80M,15M,10M,12M,30M,6M' } };   /* 1001 on 20 m already = no chip; 1003 on 17 m = 8/10 ALMOST */
(async () => {
  const b = await chromium.launch();
  for (const page of ['kpc-hunt.html', 'kpc-hunters.html']) {
    for (const vp of [{ width: 1280, height: 900, n: 'desk' }, { width: 390, height: 844, n: 'phone' }]) {
      console.log(`== ${page} (${vp.n})`);
      const errs = [];
      const ctx = await b.newContext({ viewport: { width: vp.width, height: vp.height } }); const P = await ctx.newPage();
      P.on('pageerror', e => { if (!NET.test(e.message)) errs.push('PE ' + e.message); }); P.on('console', m => { if (m.type() === 'error' && !NET.test(m.text())) errs.push(m.text()); });
      await P.route(/api\.pota\.app\/spot\/activator/, r => r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(SPOTS) }));
      await P.route(/api2\.sota\.org\.uk\/api\/spots|spothole\.app/, r => r.fulfill({ status: 200, contentType: 'application/json', body: '[]' }));
      await P.addInitScript(c => {
        localStorage.setItem('kpcHuntCounts', JSON.stringify(c));
        localStorage.setItem('kpcHuntF', JSON.stringify({ v: 3, view: 'cards', p: ['POTA'], hide: false, qrt: false, nw: false, rg: false, bands: [], modes: [], where: 'all', st: '', q: '', sort: 'new' }));
        localStorage.setItem('kpcMyCall', '"Q4LNG"');
        localStorage.setItem('kpcVipOK', 'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab');   /* the unlock hash already in kpc-vip.js (not a password) */
      }, COUNTS);
      await P.goto(BASE + page);
      const VIP = page === 'kpc-hunt.html';
      ok(await until(() => P.evaluate(() => document.querySelectorAll('.hs[data-k]').length >= 4), 15000), 'the 4 pretend spots show up');
      const chips = await P.evaluate(() => Object.fromEntries([...document.querySelectorAll('.hs[data-k]')].map(c => [c.dataset.k.split('|')[2], [...c.querySelectorAll('.hs-aw .ac')].map(a => a.textContent.trim() + (a.classList.contains('flash') ? ' [flash]' : ''))])));
      if (VIP) {
        console.log('     ' + JSON.stringify(chips));
        const A = chips['US-1001'] || [], B = chips['US-1002'] || [], C = chips['US-1003'] || [], D = chips['US-1004'] || [];
        ok(A.some(x => /🔁 Park 17\/20 · ALMOST \[flash\]/.test(x)), '🔁 Repeat Offender: 17 of 20 at US-1001, ALMOST + flashing');
        ok(A.some(x => /🤝 Q4AAA 4\/50$/.test(x)), '🤝 Op to Op: 4 of 50 with Q4AAA, not flashing');
        ok(!A.some(x => /📶/.test(x)), '📶 N1CC: no chip when you already have that band at that park');
        ok(B.some(x => /🔁 Park 3\/20$/.test(x)) && B.some(x => /🤝 Q4BBB 47\/50 · ALMOST \[flash\]/.test(x)), '🤝 Op to Op: 47 of 50 with Q4BBB, ALMOST + flashing');
        ok(C.some(x => /📶 NEW BAND 8\/10 · ALMOST \[flash\]/.test(x)) && C.some(x => /🔁 Park 41\/60$/.test(x)) && C.some(x => /🤝 Q4CCC 120\/150$/.test(x)), '📶 N1CC: 17 m is a NEW BAND at US-1003, 8 of 10, ALMOST + flashing');
        ok(D.length === 0, 'a park you have never worked gets no award chips');
        /* table view shows the short chips too */
        await P.evaluate(() => document.querySelector('[data-view="table"]').click()); await sleep(400);
        const t = await P.evaluate(() => [...document.querySelectorAll('tr.hr .ac')].map(a => a.textContent.trim()));
        ok(t.some(x => /🔁 17\/20/.test(x)) && t.some(x => /🤝 47\/50/.test(x)) && t.some(x => /📶 NEW BAND 8\/10/.test(x)), 'TABLE view shows the short award chips: ' + t.length);
        await P.evaluate(() => document.querySelector('[data-view="cards"]').click()); await sleep(400);
        /* tap a badge = the legend */
        await P.evaluate(() => document.querySelector('.hs-aw .ac').click());
        ok(await until(() => P.evaluate(() => !document.getElementById('awModal').hidden), 2000), 'tapping a badge opens “what the badges mean”');
        const leg = await P.evaluate(() => document.getElementById('awModal').textContent);
        ok(/Repeat Offender/i.test(leg) && /Operator/i.test(leg) && /N1CC/i.test(leg), 'the legend explains Repeat Offender, Op to Op and N1CC');
        if (SHOT) await P.screenshot({ path: `${SHOT}/badges-legend-${vp.n}.png` });
        await P.evaluate(() => document.querySelector('#awModal [data-mclose]').click()); await sleep(300);
        ok(await P.evaluate(() => document.getElementById('awModal').hidden), 'and it closes');
        ok(await P.evaluate(() => !!document.querySelector('.hl-awq') && getComputedStyle(document.querySelector('.hl-awq')).display !== 'none'), '🏅 BADGES? button is on the VIP list bar');
      } else {
        ok(Object.values(chips).every(L => !L.length), 'public lounge: no member award chips (as before)');
      }
      if (SHOT) await P.screenshot({ path: `${SHOT}/badges-${page.replace('.html', '')}-${vp.n}.png` });
      ok(!errs.length, 'no page errors' + (errs.length ? ': ' + errs.slice(0, 3).join(' | ') : ''));
      await ctx.close();
    }
  }
  await b.close();
  console.log(fails ? `\n${fails} FAILED` : '\nALL PASSED'); process.exit(fails ? 1 : 0);
})();
