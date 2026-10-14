// Print the KPC web guides to PDF (same filenames as the old PDFs, so every link keeps working).
// Usage: node .github/scripts/kpc_guide_pdf.js [outDir]   (serve the repo on http://localhost:8765 first)
// Needs playwright (chromium). A page signals it is ready by setting <html data-ready="1">.
const { chromium } = require('playwright');
const path = require('path');
const BASE = process.env.KPC_BASE || 'http://localhost:8765/';
const OUT = process.argv[2] || '.';
const GUIDES = [
  ['kpc-guide-pota.html?order=num', 'KPC_Kentucky_POTA_Resource_Numerical_v2_261005_092033.pdf'],
  ['kpc-guide-pota.html?order=az', 'KPC_Kentucky_POTA_Resource_Alphabetical_v2_261005_092105.pdf'],
  ['kpc-guide-sota.html', 'KPC_Kentucky_SOTA_W4K_Resource.pdf'],
  ['kpc-guide-wwff.html', 'KPC_Kentucky_WWFF_KFF_Resource.pdf'],
  ['kpc-guide-top25.html', 'KPC_Top_25_Lowest_QSO_and_Activations_October_2026_261005_084249.pdf'],
  ['kpc-guide-tools-links.html', 'KPC_Tools_and_Essential_Links.pdf'],
  ['kpc-guide-founders-favorites.html', 'KPC_Founders_Favorites_Apps_and_Tools.pdf'],
  ['kpc-guide-beginners.html', 'KPC_Beginners_Guide_to_Portable_Operations_261005_092000.pdf'],
  ['kpc-guide-antenna-efficiency.html', 'KPC_Antenna_Efficiency_Solar_Minimum_261005_091927.pdf'],
  // The Safety Guide keeps its original illustrated PDF; it is not printed from the web page.
];
(async () => {
  const only = process.env.KPC_ONLY ? process.env.KPC_ONLY.split(',') : null;
  const browser = await chromium.launch(process.env.KPC_CHROME ? { executablePath: process.env.KPC_CHROME } : {});
  let bad = 0;
  for (const [url, pdf] of GUIDES) {
    if (only && !only.some(o => url.includes(o))) continue;
    const page = await browser.newPage({ viewport: { width: 1100, height: 1400 } });
    // Block outside requests (fonts/analytics) that could stall printing on the runner.
    await page.route('**/*', r => r.request().url().startsWith(BASE) || r.request().url().startsWith('data:') ? r.continue() : r.abort());
    try {
      await page.goto(BASE + url, { waitUntil: 'load', timeout: 60000 });
      await page.waitForFunction(() => document.documentElement.dataset.ready, null, { timeout: 60000 });
      const st = await page.evaluate(() => document.documentElement.dataset.ready);
      if (st !== '1') throw new Error('page says ' + st);
      await page.emulateMedia({ media: 'print' });
      await page.pdf({ path: path.join(OUT, pdf), format: 'Letter', printBackground: true, preferCSSPageSize: true });
      console.log('printed', pdf);
    } catch (e) {
      bad++; console.log(`::warning title=Guide PDF not printed::${url}: ${e.message}`);
    }
    await page.close();
  }
  await browser.close();
  process.exit(bad ? 1 : 0);
})();
