const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const data = await page.evaluate(() => {
    const edgePaths = [...document.querySelectorAll('#diagram svg g.edgePaths path')].map(p => ({ id: p.id, d: p.getAttribute('d') }));
    const edgeLabels = [...document.querySelectorAll('#diagram svg g.edgeLabels g.edgeLabel')].map(g => ({ id: g.id || null, text: g.textContent.trim(), transform: g.getAttribute('transform') }));
    const clusters = [...document.querySelectorAll('#diagram svg g.cluster')].map(g => ({ id: g.id, transform: g.getAttribute('transform') }));
    return { edgePaths, edgeLabels, clusters };
  });
  console.log(JSON.stringify(data, null, 2));
  await browser.close();
})();