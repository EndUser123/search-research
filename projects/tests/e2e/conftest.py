"""Playwright E2E test fixtures and utilities."""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:3000")
HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))
SLOW_MO = int(os.getenv("SLOW_MO", "0"))

# Artifact directory
ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "test_artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


# ============================================================================
# Browser Fixtures
# ============================================================================


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Launch browser once per session, reuse across tests."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS, slow_mo=SLOW_MO)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """New browser context per test (isolated session/cookies)."""
    context = await browser.new_context()
    yield context
    await context.close()


@pytest.fixture(scope="function")
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """New page per test."""
    page = await context.new_page()
    yield page
    await page.close()


# ============================================================================
# PlaywrightPage Helper Class
# ============================================================================


class PlaywrightPage:
    """Wrapper around Playwright Page with convenience methods."""

    def __init__(self, page: Page, test_name: str):
        """Initialize with page instance and test name for artifacts."""
        self.page = page
        self.test_name = test_name
        self.base_url = BASE_URL

    async def goto(self, path: str) -> None:
        """Navigate to path relative to BASE_URL."""
        url = f"{self.base_url}{path}"
        await self.page.goto(url, wait_until="networkidle")

    async def fill(self, selector: str, text: str) -> None:
        """Fill form field with text."""
        await self.page.fill(selector, text)

    async def click(self, selector: str) -> None:
        """Click element and wait for network."""
        await self.page.click(selector)
        await self.page.wait_for_load_state("networkidle")

    async def type_text(self, selector: str, text: str) -> None:
        """Type slowly (human-like) in field."""
        await self.page.locator(selector).type(text, delay=50)

    async def wait_for_element(self, selector: str, timeout: int = TIMEOUT) -> None:
        """Wait for element to appear."""
        await self.page.locator(selector).wait_for(timeout=timeout)

    async def is_visible(self, selector: str) -> bool:
        """Check if element is visible."""
        return await self.page.locator(selector).is_visible()

    async def text_content(self, selector: str) -> str:
        """Get element text content."""
        return await self.page.locator(selector).text_content()

    async def verify_success_state(self, expected_text: str = None) -> None:
        """
        Assert no console errors and optionally check for text.
        Called at end of test to verify success.
        """
        # Check for JavaScript errors
        errors = []
        self.page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )

        if errors:
            raise AssertionError(f"Console errors detected: {errors}")

        # Check for expected text if provided
        if expected_text:
            content = await self.page.content()
            if expected_text not in content:
                raise AssertionError(
                    f"Expected text '{expected_text}' not found in page"
                )

    async def screenshot_element(self, selector: str, filename: str) -> None:
        """Screenshot specific element to artifacts directory."""
        locator = self.page.locator(selector)
        await locator.screenshot(path=ARTIFACTS_DIR / filename)

    async def screenshot_page(self, filename: str = None) -> None:
        """Screenshot entire page."""
        if filename is None:
            filename = f"{self.test_name}_screenshot.png"
        await self.page.screenshot(path=ARTIFACTS_DIR / filename)

    async def save_html(self, filename: str = None) -> None:
        """Save page HTML for debugging."""
        if filename is None:
            filename = f"{self.test_name}_page.html"
        content = await self.page.content()
        (ARTIFACTS_DIR / filename).write_text(content)


# ============================================================================
# Web Page Fixture
# ============================================================================


@pytest.fixture(scope="function")
async def web_page(page: Page, request) -> PlaywrightPage:
    """Provide PlaywrightPage helper with auto-failure handling."""
    wrapper = PlaywrightPage(page, request.node.name)

    yield wrapper

    # On test failure, auto-capture artifacts
    if request.node.rep_call.failed:  # type: ignore
        try:
            await wrapper.screenshot_page(f"{request.node.name}_failure.png")
            await wrapper.save_html(f"{request.node.name}_failure.html")
        except Exception as e:
            print(f"Failed to capture artifacts: {e}")


# ============================================================================
# Test Report Hook (for failure details)
# ============================================================================


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach test result info for failure handling."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
