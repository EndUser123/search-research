const { chromium } = require('playwright');
(async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 1800 } });
  await page.goto('http://localhost:18934/diagram.html', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const svgEl = document.querySelector('#diagram svg');
    const l4Node = svgEl.querySelector('g.node#flowchart-L4_S2-10');
    const l5Node = svgEl.querySelector('g.node#flowchart-L5_S1-11');
    const releaseCluster = svgEl.querySelector('g.cluster#L5');
    if (!l4Node || !l5Node || !releaseCluster) return;
    const l4Box = l4Node.getBBox();
    const l5Box = l5Node.getBBox();
    const targetTop = l4Box.y + l4Box.height + 40;
    const deltaY = targetTop - l5Box.y;
    if (deltaY <= 0) return;
    releaseCluster.setAttribute('transform', `translate(0, ${deltaY})`);
    Array.from(svgEl.querySelectorAll('g.node')).forEach(node => {
      const id = node.id || '';
      if (id.startsWith('flowchart-L5_')) {
        node.setAttribute('transform', `translate(0, ${deltaY})`);
      }
    });
    const edgePaths = Array.from(svgEl.querySelectorAll('g.edgePaths path'));
    const edgeLabels = Array.from(svgEl.querySelectorAll('g.edgeLabels g.edgeLabel'));
    edgePaths.forEach((path, index) => {
      const edgeId = path.getAttribute('id') || '';
      if (!edgeId.includes('L5')) return;
      path.setAttribute('transform', `translate(0, ${deltaY})`);
      const label = edgeLabels[index];
      if (label) label.setAttribute('transform', `translate(0, ${deltaY})`);
    });
  });
  await page.screenshot({ path: 'P:/tmp-l5-node-shift.png', fullPage: true });
  await browser.close();
})();