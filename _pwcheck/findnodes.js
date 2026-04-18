const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const matches = [];
    document.querySelectorAll('#diagram svg g').forEach(g => {
      const text = g.textContent.trim();
      if (text.includes('/commit') || text.includes('/push') || text.includes('/verify')) {
        matches.push({ cls: g.getAttribute('class'), id: g.id || null, text: text.slice(0,100) });
      }
    });
    return matches;
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();