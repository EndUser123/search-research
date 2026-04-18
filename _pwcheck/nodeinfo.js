const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const ids = ['L5_S1','L5_S2','L4_S1','L4_S2'];
    return ids.map(id => {
      const el = document.getElementById(id);
      return {
        id,
        tag: el?.tagName || null,
        parentTag: el?.parentElement?.tagName || null,
        parentId: el?.parentElement?.id || null,
        grandTag: el?.parentElement?.parentElement?.tagName || null,
        grandId: el?.parentElement?.parentElement?.id || null,
        outer: el?.outerHTML?.slice(0, 200) || null,
      };
    });
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();