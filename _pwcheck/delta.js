const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  const info = await page.evaluate(() => {
    const svgEl = document.querySelector('#diagram svg');
    const l4Node = svgEl.querySelector('g.node#flowchart-L4_S2-10');
    const l5Node = svgEl.querySelector('g.node#flowchart-L5_S1-11');
    const l4 = l4Node.getBBox();
    const l5 = l5Node.getBBox();
    return { l4, l5, delta: (l4.y + l4.height + 32) - l5.y, nodeTransform: l5Node.getAttribute('transform') };
  });
  console.log(JSON.stringify(info, null, 2));
  await browser.close();
})();