import { chromium } from 'playwright';

async function debugTextareaConstraints() {
  console.log('🔍 Debugging textarea constraints...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('[data-panel-key="sourceUrls"]', { timeout: 10000 });

    console.log('✅ VIP loaded successfully');

    // Comprehensive analysis
    const analysis = await page.evaluate(() => {
      const sourceUrlsPanel = document.querySelector('[data-panel-key="sourceUrls"]');
      const textarea = document.querySelector('[data-panel-key="sourceUrls"] textarea');
      const container = document.querySelector('[data-panel-key="sourceUrls"] .flex-grow.overflow-hidden');

      if (!sourceUrlsPanel || !textarea || !container) {
        return { error: 'Required elements not found' };
      }

      // Get computed styles
      const panelStyles = window.getComputedStyle(sourceUrlsPanel);
      const textareaStyles = window.getComputedStyle(textarea);
      const containerStyles = window.getComputedStyle(container);

      // Get rect information
      const panelRect = sourceUrlsPanel.getBoundingClientRect();
      const textareaRect = textarea.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();

      // Check viewport height
      const viewportHeight = window.innerHeight;

      return {
        viewport: {
          height: viewportHeight,
          vh: viewportHeight / 100
        },
        panel: {
          element: 'sourceUrls panel',
          rect: {
            width: Math.round(panelRect.width),
            height: Math.round(panelRect.height),
            top: Math.round(panelRect.top),
            bottom: Math.round(panelRect.bottom)
          },
          styles: {
            flexGrow: panelStyles.flexGrow,
          height: panelStyles.height,
          minHeight: panelStyles.minHeight,
          maxHeight: panelStyles.maxHeight,
          display: panelStyles.display,
          flexDirection: panelStyles.flexDirection
          }
        },
        container: {
          element: 'textarea container (.flex-grow.overflow-hidden)',
          rect: {
            width: Math.round(containerRect.width),
            height: Math.round(containerRect.height),
            top: Math.round(containerRect.top),
            bottom: Math.round(containerRect.bottom)
          },
          styles: {
            height: containerStyles.height,
            minHeight: containerStyles.minHeight,
            maxHeight: containerStyles.maxHeight,
            display: containerStyles.display,
            overflow: containerStyles.overflow
          }
        },
        textarea: {
          element: 'textarea',
          rect: {
            width: Math.round(textareaRect.width),
            height: Math.round(textareaRect.height),
            top: Math.round(textareaRect.top),
            bottom: Math.round(textareaRect.bottom)
          },
          styles: {
            height: textareaStyles.height,
            minHeight: textareaStyles.minHeight,
            maxHeight: textareaStyles.maxHeight,
            lineHeight: textareaStyles.lineHeight,
            fontSize: textareaStyles.fontSize
          },
          content: {
            value: textarea.value,
            lines: textarea.value.split('\n').filter(line => line.trim()).length,
            scrollHeight: textarea.scrollHeight,
            clientHeight: textarea.clientHeight
          }
        }
      };
    });

    console.log('\n📊 COMPREHENSIVE ANALYSIS:');
    console.log(JSON.stringify(analysis, null, 2));

    // Calculate expected vs actual
    if (analysis.textarea) {
      const lineHeight = parseFloat(analysis.textarea.styles.lineHeight) || 24;
      const actualVisibleLines = Math.floor(analysis.textarea.rect.height / lineHeight);
      const expectedVisibleLines = Math.floor(analysis.textarea.rect.height / lineHeight);

      console.log('\n📏 LINE CALCULATION:');
      console.log(`  - Line height: ${lineHeight}px`);
      console.log(`  - Textarea height: ${analysis.textarea.rect.height}px`);
      console.log(`  - Expected visible lines: ${expectedVisibleLines}`);
      console.log(`  - Actual calculation: ${actualVisibleLines}`);
      console.log(`  - Total content lines: ${analysis.textarea.content.lines}`);

      if (analysis.viewport) {
        console.log('\n🖥️  VIEWPORT ANALYSIS:');
        console.log(`  - Viewport height: ${analysis.viewport.height}px`);
        console.log(`  - 1vh = ${analysis.viewport.vh}px`);
        console.log(`  - calc(50vh - 4rem) ≈ ${Math.round(analysis.viewport.height * 0.5 - 64)}px`);
      }
    }

    console.log('\n🎯 Debug completed! Browser will stay open for manual inspection.');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.error('❌ Debug failed:', error.message);
  } finally {
    await browser.close();
  }
}

debugTextareaConstraints();
