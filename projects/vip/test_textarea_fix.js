import { chromium } from 'playwright';

async function testVIPTextarea() {
  console.log('🧪 Testing VIP textarea layout fix...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to VIP
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');

    // Wait for the app to load
    await page.waitForSelector('[data-panel-key="sourceUrls"]', { timeout: 10000 });

    console.log('✅ VIP loaded successfully');

    // Test 1: Check initial textarea state
    const textarea = await page.locator('[data-panel-key="sourceUrls"] textarea');
    const textareaContainer = await page.locator('[data-panel-key="sourceUrls"] .flex-grow.overflow-hidden');

    const textareaVisible = await textarea.isVisible();
    const textareaBounds = await textarea.boundingBox();
    const containerBounds = await textareaContainer.boundingBox();

    console.log('📏 Initial textarea state:');
    console.log(`  - Visible: ${textareaVisible}`);
    console.log(`  - Textarea bounds: ${JSON.stringify(textareaBounds)}`);
    console.log(`  - Container bounds: ${JSON.stringify(containerBounds)}`);

    // Test 2: Check if textarea has proper minimum height
    if (textareaBounds && containerBounds) {
      const hasMinHeight = textareaBounds.height >= 120;
      console.log(`  - Has minimum height (>=120px): ${hasMinHeight}`);

      if (hasMinHeight) {
        console.log('✅ PASS: Textarea has proper minimum height');
      } else {
        console.log('❌ FAIL: Textarea height is too small');
      }
    }

    // Test 3: Check if URLs are visible (more than 2.5 lines)
    const lines = await textarea.inputValue();
    const lineCount = lines.split('\n').filter(line => line.trim()).length;
    console.log(`  - URL lines visible: ${lineCount}`);

    if (lineCount >= 3) {
      console.log('✅ PASS: Multiple URL lines are visible');
    } else {
      console.log('⚠️  WARNING: Fewer than 3 URL lines visible (might be empty textarea)');
    }

    // Test 4: Check panel collapse functionality
    const collapseButton = await page.locator('[data-panel-key="sourceUrls"] button').first();
    await collapseButton.click();

    // Wait for collapse animation
    await page.waitForTimeout(500);

    const isCollapsed = await page.locator('[data-panel-key="sourceUrls"]').evaluate(el => {
      return el.style.flexGrow === '0' || getComputedStyle(el).flexGrow === '0';
    });

    console.log(`🔄 Panel collapsed: ${isCollapsed}`);

    if (isCollapsed) {
      // Check if textarea is truly hidden when collapsed
      const collapsedTextareaBounds = await textarea.boundingBox();
      const isHidden = !collapsedTextareaBounds || collapsedTextareaBounds.height < 10;

      console.log(`  - Textarea hidden when collapsed: ${isHidden}`);

      if (isHidden) {
        console.log('✅ PASS: Textarea properly hidden when panel collapsed');
      } else {
        console.log('❌ FAIL: Textarea still visible when panel should be collapsed');
      }
    }

    console.log('\n🎯 Test completed! Check the browser for visual verification.');

    // Take a screenshot for manual verification
    await page.screenshot({ path: 'vip_textarea_test_result.png', fullPage: false });
    console.log('📸 Screenshot saved: vip_textarea_test_result.png');

    // Keep browser open for 10 seconds for manual inspection
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testVIPTextarea();
