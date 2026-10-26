// KPC CHECK-UP, Sunday part: the SITE TEST RUN as a GUEST (chat 5, Oct 26 2026; Brandon GO).
// Opens every PUBLIC page (kpc-gate.js) at phone width (390 px) and desktop width (1280 px) the way a guest sees it
// (navigator.webdriver is set back to false, otherwise the gate lets the robot in like a member), and checks:
//   - JavaScript errors on the page (uncaught errors = PROBLEM; console errors = note only, often a busy outside API)
//   - sideways scroll (page wider than the screen) = PROBLEM
//   - a link to a members-only page that the gate did NOT hide from the guest = PROBLEM
//   - the members door showing on a public page = PROBLEM
// It also opens a few members-only pages to make sure the door DOES show there.
// Usage: node kpc_site_test.js http://127.0.0.1:8765/KPC-Links/ checkup-out/site.json   (needs: npm i playwright)
// Never fails: any trouble is written into the report.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const BASE = process.argv[2] || 'http://127.0.0.1:8765/';
const OUTF = process.argv[3] || 'checkup-out/site.json';
const gate = fs.readFileSync('kpc-gate.js', 'utf8');
const PUBLIC = (gate.match(/var PUBLIC = \[([\s\S]*?)\];/) || ['', ''])[1].match(/'[\w.-]+\.html'/g).map(s => s.slice(1, -1));
const SWAP = Object.keys(JSON.parse(((gate.match(/var SWAP = (\{[^}]*\})/) || ['', '{}'])[1]).replace(/'/g, '"')));
const MH = (gate.match(/var MH = '([0-9a-f]{64})'/) || ['', ''])[1];      // the member key (a hash; the password itself is never here)
const MEMBER = process.env.MEMBER_PASS === '1';                         // release night: also every page as a signed-in member
const ORIGIN = new URL(BASE).origin;
const LOCKED_SAMPLE = ['parks.html', 'toolbox.html', 'find.html', 'kpc-kit.html'].filter(f => fs.existsSync(f));

function chatOf(page) {
  if (/^(kpc-hunters|kpc-beta-|kpc-spots|kpc-spot-me|kpc-campgrounds|kpc-park-notes|kpc-activat|kpc-logger|kpc-tracker|kpc-top25|kpc-rare|kpc-park-sheet)/.test(page)) return 3;
  if (/^(kpc-park-control|kpc-planner|finder|kpc-map-room|kpc-kit|kpc-info|kpc-am-i|kpc-maprep)/.test(page)) return 2;
  if (/^(campout|events|videos|kpc-calendar)/.test(page)) return 6;
  return 1;
}

(async () => {
  const problems = [], notes = [], ok = [];
  let browser;
  try {
    browser = await chromium.launch();
    const sizes = [['phone', { width: 390, height: 844 }], ['desktop', { width: 1280, height: 900 }]];
    for (const [label, viewport] of sizes) {
      const ctx = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: label === 'phone', hasTouch: label === 'phone' });
      await ctx.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => false }); });
      // outside services are not part of this test: block them so a slow API can't hold the run (the page must cope)
      await ctx.route(u => new URL(u).origin !== ORIGIN, r => r.abort());
      for (const page of PUBLIC) {
        if (!fs.existsSync(page)) continue;
        const pg = await ctx.newPage();
        const errs = [], cons = [];
        pg.on('pageerror', e => errs.push(String(e.message || e).slice(0, 160)));
        pg.on('console', m => { if (m.type() === 'error' && !/Failed to load resource|net::ERR_|ERR_FAILED|blocked by/i.test(m.text())) cons.push(m.text().slice(0, 140)); });
        try {
          await pg.goto(BASE + page, { waitUntil: 'load', timeout: 45000 });
          await pg.waitForTimeout(2500);
          const r = await pg.evaluate(({ PUBLIC, SWAP }) => {
            const out = { wide: 0, door: !!document.getElementById('kpcDoor'), shown: [] };
            const de = document.documentElement;
            out.wide = Math.max(de.scrollWidth, document.body ? document.body.scrollWidth : 0) - window.innerWidth;
            for (const a of document.querySelectorAll('a[href]')) {
              const h = a.getAttribute('href');
              if (!h || /^(#|mailto:|tel:|sms:|javascript:)/i.test(h)) continue;
              let u; try { u = new URL(h, location.href); } catch (e) { continue; }
              if (u.origin !== location.origin) continue;
              let f = (u.pathname.split('/').pop() || 'index.html').toLowerCase();
              if (!/\.html?$/.test(f)) continue;
              if (PUBLIC.includes(f) || SWAP.includes(f)) continue;
              if (a.closest('[data-kpc-hide]')) continue;
              const cs = getComputedStyle(a), rc = a.getBoundingClientRect();
              const visible = cs.display !== 'none' && cs.visibility !== 'hidden' && rc.width > 0 && rc.height > 0;
              const inMenu = !!a.closest('nav, header, .menu, .more-menu, [class*="menu"], [id*="menu"]');
              if (visible || inMenu) out.shown.push(f + (a.textContent.trim() ? ' ("' + a.textContent.trim().slice(0, 40) + '")' : ''));
            }
            out.shown = [...new Set(out.shown)];
            return out;
          }, { PUBLIC, SWAP });
          const c = chatOf(page);
          if (errs.length) problems.push({ key: `site:jserr:${page}:${label}`, chat: c, msg: `${page} (${label}): JavaScript error: ${[...new Set(errs)].slice(0, 2).join(' | ')}` });
          if (cons.length) notes.push({ chat: c, msg: `${page} (${label}): console says: ${[...new Set(cons)].slice(0, 2).join(' | ')}` });
          if (r.wide > 2) problems.push({ key: `site:wide:${page}:${label}`, chat: c, msg: `${page} (${label}): page is ${r.wide}px wider than the screen (sideways scroll)` });
          if (r.door && page !== '404.html') problems.push({ key: `site:door:${page}`, chat: 1, msg: `${page}: public page shows the members door to guests` });
          if (r.shown.length) problems.push({ key: `site:memberlink:${page}:${r.shown.slice(0, 5).join(',')}`, chat: 1, msg: `${page} (${label}): guests can see link(s) to members-only page(s): ${r.shown.slice(0, 6).join(', ')}` });
        } catch (e) {
          problems.push({ key: `site:load:${page}:${label}`, chat: chatOf(page), msg: `${page} (${label}): did not load (${String(e.message || e).slice(0, 100)})` });
        }
        await pg.close();
      }
      ok.push(`${PUBLIC.length} public pages opened as a guest at ${label} width (${viewport.width}px)`);
      if (label === 'phone') {
        for (const page of LOCKED_SAMPLE) {
          const pg = await ctx.newPage();
          try {
            await pg.goto(BASE + page, { waitUntil: 'load', timeout: 45000 });
            await pg.waitForTimeout(1500);
            const door = await pg.evaluate(() => !!document.getElementById('kpcDoor'));
            if (!door) problems.push({ key: `site:nodoor:${page}`, chat: 1, msg: `${page}: members-only page opened for a guest with NO members door` });
          } catch (e) { notes.push({ chat: 5, msg: `${page}: could not test the members door (${String(e.message || e).slice(0, 80)})` }); }
          await pg.close();
        }
        ok.push(`members door checked on ${LOCKED_SAMPLE.join(', ')}`);
      }
      await ctx.close();
    }
    if (MEMBER && MH) {
      // every page as a signed-in member at phone width: JavaScript errors and sideways scroll (the new menu is on all of them)
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
      await ctx.addInitScript(([k]) => { Object.defineProperty(navigator, 'webdriver', { get: () => false }); try { localStorage.setItem('kpcMember', k); } catch (e) {} }, [MH]);
      await ctx.route(u => new URL(u).origin !== ORIGIN, r => r.abort());
      const all = fs.readdirSync('.').filter(f => /\.html$/.test(f)).sort();
      let n = 0;
      for (const page of all) {
        const pg = await ctx.newPage();
        const errs = [];
        pg.on('pageerror', e => errs.push(String(e.message || e).slice(0, 160)));
        try {
          await pg.goto(BASE + page, { waitUntil: 'load', timeout: 45000 });
          await pg.waitForTimeout(1500);
          const r = await pg.evaluate(() => ({ wide: Math.max(document.documentElement.scrollWidth, document.body ? document.body.scrollWidth : 0) - window.innerWidth, door: !!document.getElementById('kpcDoor') }));
          const c = chatOf(page);
          if (errs.length) problems.push({ key: `site:member:jserr:${page}`, chat: c, msg: `${page} (member, phone): JavaScript error: ${[...new Set(errs)].slice(0, 2).join(' | ')}` });
          if (r.wide > 2) problems.push({ key: `site:member:wide:${page}`, chat: c, msg: `${page} (member, phone): page is ${r.wide}px wider than the screen` });
          if (r.door && page !== '404.html' && !/^kpc-beta-/.test(page)) problems.push({ key: `site:member:door:${page}`, chat: 1, msg: `${page}: a signed-in member still gets the members door` });
          n++;
        } catch (e) {
          problems.push({ key: `site:member:load:${page}`, chat: chatOf(page), msg: `${page} (member): did not load (${String(e.message || e).slice(0, 100)})` });
        }
        await pg.close();
      }
      ok.push(`${n} pages opened as a signed-in member at phone width`);
      await ctx.close();
    }
  } catch (e) {
    notes.push({ chat: 5, msg: 'Site test could not run: ' + String(e.message || e).slice(0, 200) });
  }
  if (browser) await browser.close().catch(() => {});
  fs.mkdirSync(path.dirname(OUTF), { recursive: true });
  fs.writeFileSync(OUTF, JSON.stringify({ part: 'site', date: new Date().toISOString().slice(0, 10), problems, notes, ok }, null, 1));
  console.log(`::notice title=Check-up site::${problems.length} problem(s), ${notes.length} note(s)`);
})();
