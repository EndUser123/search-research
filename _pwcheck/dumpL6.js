const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    return [...document.querySelectorAll('g.node')]
      .filter(n => (n.id || '').startsWith('flowchart-L6_'))
      .map(n => ({ id: n.id, transform: n.getAttribute('transform'), text: n.textContent.trim() }));
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();