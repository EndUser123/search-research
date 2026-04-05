# yt_sync/auth_capture.py

import asyncio
import logging
import re
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

# This block defines types for static analysis, and 'Any' for runtime.
if TYPE_CHECKING:
    from playwright.async_api import (
        BrowserContext,
        CDPSession,
        Page,
        Route,
        async_playwright,
    )
    from playwright.async_api import (
        TimeoutError as PlaywrightTimeoutError,
    )
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
else:
    # At runtime, if imports fail, these will be 'Any', which is a valid type hint.
    async_playwright = Any
    Page = Any
    Route = Any
    BrowserContext = Any
    CDPSession = Any
    PlaywrightTimeoutError = Any
    Console = Any
    Panel = Any
    Text = Any

try:
    from playwright.async_api import (
        BrowserContext,
        CDPSession,
        Page,
        Route,
        async_playwright,
    )
    from playwright.async_api import (
        TimeoutError as PlaywrightTimeoutError,
    )
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
except ImportError:
    # At runtime, if imports fail, these will be None. The TYPE_CHECKING block ensures the linter doesn't see this.
    async_playwright = (
        Page
    ) = (
        Route
    ) = (
        BrowserContext
    ) = PlaywrightTimeoutError = CDPSession = Console = Panel = Text = None


logger = logging.getLogger(__name__)


COOKIE_FILE_HEADER = """# Netscape HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file! Do not edit.

"""


class _HeaderCapturer:
    """A helper class to reliably capture authentication headers from YouTube network requests."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self.auth_headers: dict[str, str] = {}
        self.headers_found_event = asyncio.Event()
        self.required_headers: set[str] = {"Authorization", "x-youtube-identity-token"}
        self.captured_headers: set[str] = set()
        self.cdp_session: Any = None

    def _check_and_set_event(self):
        """Check if all required headers have been captured and set the event if so."""
        if self.required_headers.issubset(self.captured_headers):
            if not self.headers_found_event.is_set():
                logger.info(
                    f"✅ All required headers captured: {', '.join(self.required_headers)}"
                )
                self.headers_found_event.set()

    async def setup_monitoring(self, page):
        """Set up all monitoring mechanisms for maximum reliability."""
        await self._setup_cdp_monitoring(page)
        await self._setup_route_interception(page)
        logger.debug("All header monitoring mechanisms have been set up.")

    async def _setup_cdp_monitoring(self, page):
        """Set up CDP session to monitor all network requests (most reliable method)."""
        try:
            self.cdp_session = await page.context.new_cdp_session(page)
            assert self.cdp_session is not None
            await self.cdp_session.send("Network.enable")
            self.cdp_session.on("Network.requestWillBeSent", self._handle_cdp_request)
            logger.debug("CDP monitoring enabled.")
        except Exception as e:
            logger.warning(
                f"Could not set up CDP monitoring: {e}. Relying on fallback methods."
            )

    # --- THIS IS THE BUG FIX: REMOVED 'async' ---
    def _handle_cdp_request(self, event: dict[str, Any]):
        """Handle a CDP Network.requestWillBeSent event."""
        headers = event.get("request", {}).get("headers", {})
        for header_name in self.required_headers:
            if (
                header_name.lower() in {k.lower() for k in headers}
                and header_name not in self.captured_headers
            ):
                value = next(
                    (v for k, v in headers.items() if k.lower() == header_name.lower()),
                    None,
                )
                if value:
                    self.auth_headers[header_name] = value
                    self.captured_headers.add(header_name)
                    logger.debug(f"CDP captured header: {header_name}")
        self._check_and_set_event()

    async def _setup_route_interception(self, page):
        """Set up request interception as a fallback mechanism."""
        patterns = ["**/youtubei/v1/**", "**youtube.com/api/**"]
        for pattern in patterns:
            await page.route(pattern, self._handle_route)
        logger.debug(f"Route interception fallback set up for: {', '.join(patterns)}")

    async def _handle_route(self, route):
        """Handle an intercepted request via page.route()."""
        headers = await route.request.all_headers()
        for header_name in self.required_headers:
            if header_name in headers and header_name not in self.captured_headers:
                self.auth_headers[header_name] = headers[header_name]
                self.captured_headers.add(header_name)
                logger.debug(f"Route interception captured header: {header_name}")
        self._check_and_set_event()
        await route.continue_()

    async def wait_for_headers(self) -> dict[str, str]:
        """Wait for all required authentication headers to be captured."""
        try:
            await asyncio.wait_for(
                self.headers_found_event.wait(), timeout=self.timeout
            )
            return self.auth_headers
        except TimeoutError:
            captured = ", ".join(self.captured_headers) or "none"
            missing = ", ".join(self.required_headers - self.captured_headers)
            logger.warning(
                f"Timed out waiting for auth headers. Captured: [{captured}], Missing: [{missing}]."
            )
            return self.auth_headers  # Return what we have

    async def cleanup(self):
        """Clean up resources."""
        if self.cdp_session:
            try:
                await self.cdp_session.detach()
                logger.debug("CDP session detached.")
            except Exception as e:
                logger.debug(f"Error detaching CDP session: {e}")


class AuthCapturer:
    def __init__(self, video_url: str):
        if not all([async_playwright, Console, Panel, Text]):
            raise ImportError(
                "Required libraries (playwright, rich) are not installed. Please run: pip install playwright rich"
            )

        self.video_url = video_url
        assert Console is not None
        self.console = Console()

    def _convert_cookies_to_netscape(self, cookies: Sequence[Any]) -> str:
        netscape_cookies = [COOKIE_FILE_HEADER]
        for cookie in cookies:
            domain = cookie.get("domain", "")
            tailmatch = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expires = (
                str(int(cookie.get("expires", 0)))
                if cookie.get("expires", -1) != -1
                else "0"
            )
            name = re.sub(r"\s+", " ", str(cookie.get("name", "")))
            value = re.sub(r"\s+", " ", str(cookie.get("value", "")))
            if not all([domain, name]):
                continue
            line = (
                f"{domain}\t{tailmatch}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
            )
            netscape_cookies.append(line)
        return "\n".join(netscape_cookies)

    def _print_instructions(self):
        assert Text is not None and Panel is not None and self.console is not None
        instructions = Text(
            "A browser window will now open.\n\n"
            "1. You may be redirected to a Google Sign-in page. Please complete the login.\n"
            "2. Handle any CAPTCHA or 2FA prompts.\n"
            "3. The script will wait for you to be redirected back to the YouTube video page.\n\n"
            "You can close the browser window at any time to cancel.",
            justify="left",
        )
        self.console.print(
            Panel(
                instructions,
                title="[bold yellow]Interactive Login Required[/bold yellow]",
                expand=False,
            )
        )

    async def run_async(self) -> dict[str, Any] | None:
        assert (
            async_playwright is not None
        ), "Playwright library is not installed. Please run: pip install playwright"
        assert (
            PlaywrightTimeoutError is not None
        ), "Playwright library is not installed. Please run: pip install playwright"
        self._print_instructions()

        playwright = await async_playwright().start()
        browser = None
        header_capturer = _HeaderCapturer()

        try:
            browser = await playwright.chromium.launch(
                headless=False, args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            await header_capturer.setup_monitoring(page)

            logger.info(f"Navigating to video URL: {self.video_url}")
            await page.goto(
                self.video_url, wait_until="domcontentloaded", timeout=90000
            )

            self.console.print(
                "Waiting for you to complete the login process in the browser..."
            )

            await page.wait_for_function(
                """
                () => {
                    const isCorrectURL = window.location.href.includes('youtube.com/watch') && !window.location.href.includes('accounts.google.com');
                    const playerVisible = document.querySelector('#movie_player')?.offsetParent !== null;
                    return isCorrectURL && playerVisible;
                }
            """,
                timeout=300000,
            )

            self.console.print(
                "✅ Login successful and player is visible. Waiting for auth headers..."
            )

            auth_headers = await header_capturer.wait_for_headers()

            cookies_path = Path("cookies.txt").resolve()
            cookies = await context.cookies()

            if not cookies:
                self.console.print(
                    "[bold red]❌ Failed to capture any cookies. Authentication may have been incomplete. Aborting.[/bold red]"
                )
                return None

            auth_result: dict[str, Any] = {"cookies_file": str(cookies_path)}
            if auth_headers:
                auth_result["http_headers"] = auth_headers

            with open(cookies_path, "w", encoding="utf-8") as f:
                f.write(self._convert_cookies_to_netscape(cookies))

            return auth_result

        except PlaywrightTimeoutError:
            self.console.print(
                "[bold red]❌ Timed out waiting for you to complete the login. Please try again.[/bold red]"
            )
            return None
        except Exception as e:
            logger.error(
                f"An unexpected error occurred during auth capture: {e}", exc_info=True
            )
            return None
        finally:
            await header_capturer.cleanup()
            if browser:
                await browser.close()
            await playwright.stop()
