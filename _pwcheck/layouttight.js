const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1800);
  const info = await page.evaluate(() => {
    const rect = sel => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, width: r.width, height: r.height };
    };
    return ['L1','L2','L3','L4','L5','L6'].map(id => ({ id, rect: rect(`g.cluster#${id}`) }));
  });
  console.log(JSON.stringify(info, null, 2));
  await page.screenshot({ path: 'P:/tmp-layout-tight.png', fullPage: true });
  await browser.close();
})();