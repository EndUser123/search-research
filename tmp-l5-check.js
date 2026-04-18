const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const rect = sel => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: r.x, y: r.y, width: r.width, height: r.height };
    };
    return {
      l4: rect('g.cluster#L4'),
      l5: rect('g.cluster#L5'),
      l6: rect('g.cluster#L6'),
    };
  });
  console.log(JSON.stringify(info, null, 2));
  await page.screenshot({ path: 'P:/tmp-l5-check.png', fullPage: true });
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });