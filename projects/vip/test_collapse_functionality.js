import { chromium } from 'playwright';

async function testCollapseFunctionality() {
  console.log('🔍 Testing panel collapse to 0 height...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-panel-key="sourceUrls"]', { timeout: 10000 });

    console.log('✅ VIP loaded successfully');

    // Test 1: Check initial state
    const initialState = await page.evaluate(() => {
      const panel = document.querySelector('[data-panel-key="sourceUrls"]');
      const textarea = document.querySelector('[data-panel-key="sourceUrls"] textarea');
      const collapseButton = document.querySelector('[data-panel-key="sourceUrls"] button');

      if (!panel || !textarea || !collapseButton) {
        return { error: 'Required elements not found' };
      }

      const panelRect = panel.getBoundingClientRect();
      const textareaRect = textarea.getBoundingClientRect();

      return {
        panelHeight: Math.round(panelRect.height),
        textareaHeight: Math.round(textareaRect.height),
        panelCollapsed: panel.style.flexGrow === '0' || getComputedStyle(panel).flexGrow === '0',
        textareaVisible: textareaRect.height > 0
      };
    });

    console.log('\n📊 Initial State:');
    console.log(`  Panel height: ${initialState.panelHeight}px`);
    console.log(`  Textarea height: ${initialState.textareaHeight}px`);
    console.log(`  Panel collapsed: ${initialState.panelCollapsed}`);
    console.log(`  Textarea visible: ${initialState.textareaVisible}`);

    // Test 2: Try to collapse the panel
    console.log('\n🔄 Attempting to collapse panel...');

    const collapseResult = await page.evaluate(async () => {
      const collapseButton = document.querySelector('[data-panel-key="sourceUrls"] button');
      const panel = document.querySelector('[data-panel-key="sourceUrls"]');

      if (!collapseButton || !panel) {
        return { error: 'Elements not found' };
      }

      // Click collapse button
      collapseButton.click();

      // Wait for animation
      await new Promise(resolve => setTimeout(resolve, 500));

      const panelRect = panel.getBoundingClientRect();
      const textarea = document.querySelector('[data-panel-key="sourceUrls"] textarea');
      const textareaRect = textarea ? textarea.getBoundingClientRect() : { height: 0 };

      return {
        panelHeight: Math.round(panelRect.height),
        textareaHeight: Math.round(textareaRect.height),
        panelCollapsed: panel.style.flexGrow === '0' || getComputedStyle(panel).flexGrow === '0',
        textareaVisible: textareaRect.height > 0
      };
    });

    console.log('\n📊 After Collapse:');
    console.log(`  Panel height: ${collapseResult.panelHeight}px`);
    console.log(`  Textarea height: ${collapseResult.textareaHeight}px`);
    console.log(`  Panel collapsed: ${collapseResult.panelCollapsed}`);
    console.log(`  Textarea visible: ${collapseResult.textareaVisible}`);

    // Test 3: Try to use slider to collapse further
    console.log('\n🔄 Attempting to use slider to collapse to 0...');

    const sliderResult = await page.evaluate(async () => {
      // Find the slider element (it should be after the panel)
      const panel = document.querySelector('[data-panel-key="sourceUrls"]');
      if (!panel) return { error: 'Panel not found' };

      // Try to find a slider or resize handle after this panel
      const siblings = Array.from(panel.parentElement.children);
      const sliderElement = siblings.find((el, index) =>
        siblings[index - 1] === panel &&
        (el.classList.contains('resize-handle') || el.style.cursor === 'row-resize' || el.tagName === 'DIV')
      );

      if (!sliderElement) {
        return { error: 'Slider element not found' };
      }

      const sliderRect = sliderElement.getBoundingClientRect();

      // Try to drag slider up to collapse
      const startY = sliderRect.top + sliderRect.height / 2;
      const endY = startY - 100; // Move up significantly

      // Simulate drag
      const mouseDown = new MouseEvent('mousedown', {
        bubbles: true,
        cancelable: true,
        clientX: sliderRect.left + sliderRect.width / 2,
        clientY: startY
      });

      sliderElement.dispatchEvent(mouseDown);

      await new Promise(resolve => setTimeout(resolve, 100));

      const mouseMove = new MouseEvent('mousemove', {
        bubbles: true,
        cancelable: true,
        clientX: sliderRect.left + sliderRect.width / 2,
        clientY: endY
      });

      document.dispatchEvent(mouseMove);

      await new Promise(resolve => setTimeout(resolve, 200));

      const mouseUp = new MouseEvent('mouseup', {
        bubbles: true,
        cancelable: true,
        clientX: sliderRect.left + sliderRect.width / 2,
        clientY: endY
      });

      document.dispatchEvent(mouseUp);

      await new Promise(resolve => setTimeout(resolve, 500));

      const finalPanelRect = panel.getBoundingClientRect();
      const textarea = document.querySelector('[data-panel-key="sourceUrls"] textarea');
      const finalTextareaRect = textarea ? textarea.getBoundingClientRect() : { height: 0 };

      return {
        panelHeight: Math.round(finalPanelRect.height),
        textareaHeight: Math.round(finalTextareaRect.height),
        panelCollapsed: panel.style.flexGrow === '0' || getComputedStyle(panel).flexGrow === '0',
        textareaVisible: finalTextareaRect.height > 0,
        sliderFound: true
      };
    });

    console.log('\n📊 After Slider Attempt:');
    console.log(`  Panel height: ${sliderResult.panelHeight}px`);
    console.log(`  Textarea height: ${sliderResult.textareaHeight}px`);
    console.log(`  Panel collapsed: ${sliderResult.panelCollapsed}`);
    console.log(`  Textarea visible: ${sliderResult.textareaVisible}`);
    console.log(`  Slider found: ${sliderResult.sliderFound}`);

    console.log('\n🎯 Test completed! Browser will stay open for manual verification.');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('❌ Test failed:', error.message);
  } finally {
    await browser.close();
  }
}

testCollapseFunctionality();
