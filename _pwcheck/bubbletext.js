const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1200 } });
  await page.goto('file:///P:/packages/search-research/diagram.html?layout=TB&zoom=1&corner=bl', { waitUntil: 'load' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'P:/tmp-bubble-text-bigger.png', fullPage: true });
  await browser.close();
})();