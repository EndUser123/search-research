import { chromium } from 'playwright';

async function testVisibleLines() {
  console.log('🔍 Testing VIP textarea visible lines...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to VIP
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-panel-key="sourceUrls"]', { timeout: 10000 });

    console.log('✅ VIP loaded successfully');

    // Test 1: Check how many lines are actually visible
    const textarea = await page.locator('[data-panel-key="sourceUrls"] textarea');

    const visibleInfo = await textarea.evaluate((el) => {
      const rect = el.getBoundingClientRect();
      const computedStyle = window.getComputedStyle(el);
      const lineHeight = parseFloat(computedStyle.lineHeight) || 20; // fallback

      // Calculate how many lines can fit
      const visibleLines = Math.floor(rect.height / lineHeight);

      return {
        rect: {
          width: Math.round(rect.width),
          height: Math.round(rect.height)
        },
        lineHeight: Math.round(lineHeight),
        visibleLines,
        actualContent: el.value,
        contentLines: el.value.split('\n').filter(line => line.trim()).length
      };
    });

    console.log('\n📏 Textarea Analysis:');
    console.log(`  - Dimensions: ${visibleInfo.rect.width}x${visibleInfo.rect.height}px`);
    console.log(`  - Line height: ${visibleInfo.lineHeight}px`);
    console.log(`  - Visible lines: ${visibleInfo.visibleLines}`);
    console.log(`  - Total content lines: ${visibleInfo.contentLines}`);

    // Test 2: Try expanding the panel using slider
    console.log('\n🔄 Attempting to expand panel using slider...');

    // Find and drag the slider to increase panel height
    const slider = await page.locator('[data-panel-key="sourceUrls"] + div').first();

    if (await slider.isVisible()) {
      const sliderBounds = await slider.boundingBox();
      if (sliderBounds) {
        // Drag slider down to expand panel
        await page.mouse.move(sliderBounds.x + sliderBounds.width / 2, sliderBounds.y + sliderBounds.height / 2);
        await page.mouse.down();
        await page.mouse.move(sliderBounds.x + sliderBounds.width / 2, sliderBounds.y + 100, { steps: 10 });
        await page.mouse.up();

        // Wait for layout to settle
        await page.waitForTimeout(500);

        // Check expanded state
        const expandedInfo = await textarea.evaluate((el) => {
          const rect = el.getBoundingClientRect();
          const computedStyle = window.getComputedStyle(el);
          const lineHeight = parseFloat(computedStyle.lineHeight) || 20;
          const visibleLines = Math.floor(rect.height / lineHeight);

          return {
            rect: {
              width: Math.round(rect.width),
              height: Math.round(rect.height)
            },
            lineHeight: Math.round(lineHeight),
            visibleLines
          };
        });

        console.log('\n📏 After Expansion:');
        console.log(`  - Dimensions: ${expandedInfo.rect.width}x${expandedInfo.rect.height}px`);
        console.log(`  - Visible lines: ${expandedInfo.visibleLines}`);
      }
    } else {
      console.log('❌ Slider not found or not visible');
    }

    console.log('\n🎯 Test completed! Check the browser for visual verification.');
    await page.waitForTimeout(5000);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testVisibleLines();
