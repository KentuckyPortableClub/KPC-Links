const { chromium } = require('playwright');
const S = process.argv[2];
const pages = ['index', 'campoutHOLD', 'eventsHOLD', 'kentucky-parks', 'kpc-park-control', 'kpc-park-notes', 'kpc-guide-pota', 'kpc-campgrounds', 'kpc-spots', 'kpc-community', 'join'];
(async () => {
  const b = await chromium.launch();
  for (const [vw, vh, tag] of [[1440, 900, 'd'], [390, 844, 'm']]) {
    const c = await b.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: tag === 'm' ? 2 : 1 });
    await c.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => false }); });
    const p = await c.newPage();
    for (const n of pages) {
      try { await p.goto('http://localhost:8765/' + n + '.html', { waitUntil: 'load', timeout: 20000 }); } catch (e) {}
      await p.waitForTimeout(2500);
      await p.evaluate(() => { document.querySelectorAll('[class*="cookie"],[id*="cookie"]').forEach(e => e.remove()); });
      const h = await p.evaluate(() => Math.min(document.documentElement.scrollHeight, 4200));
      await p.setViewportSize({ width: vw, height: tag === 'm' ? vh : h });
      await p.waitForTimeout(800);
      await p.screenshot({ path: `${S}/${n}-${tag}.png`, fullPage: false });
      await p.setViewportSize({ width: vw, height: vh });
    }
    await c.close();
  }
  await b.close();
})();
