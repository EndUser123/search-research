const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  const info = await page.evaluate(() => {
    const sels = ['g.cluster#L5','g.node#flowchart-L5_S1-11','g.node#flowchart-L5_S2-12','g.node#flowchart-L4_S2-10','g.edgePaths path#L-L4_S2-L5_S1-0'];
    return sels.map(sel => {
      const el = document.querySelector(sel);
      return { sel, transform: el?.getAttribute('transform') || null, tag: el?.tagName || null, id: el?.id || null };
    });
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();