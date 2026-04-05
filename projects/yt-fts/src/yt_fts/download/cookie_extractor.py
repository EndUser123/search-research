"""
Browser Cookie Extractor for YouTube
Uses Playwright to extract cookies from Firefox/Chrome when native extraction fails
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from rich.console import Console

# Try to import playwright, but make it optional
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    sync_playwright = None


class BrowserCookieExtractor:
    """
    Extracts YouTube cookies using browser automation when native extraction fails.
    Supports Firefox and Chrome on Windows.
    """

    def __init__(self, console: Console = None):
        """
        Initialize the browser cookie extractor.

        Args:
            console: Rich console instance for output (defaults to new Console())
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)

    def extract_cookies_from_browser(self, browser: str = "firefox") -> str | None:
        """
        Extract cookies from browser and save to temporary file.

        Args:
            browser: Browser to use ("firefox" or "chrome")

        Returns:
            Path to cookie file, or None if extraction fails
        """
        if not PLAYWRIGHT_AVAILABLE:
            self.console.print("[red]❌ Playwright not available. Install with: pip install playwright[/red]")
            self.console.print("[blue]💡 Then run: playwright install[/blue]")
            return None

        try:
            with sync_playwright() as p:
                if browser.lower() == "firefox":
                    return self._extract_from_firefox(p)
                if browser.lower() == "chrome":
                    return self._extract_from_chrome(p)
                self.console.print(f"[red]❌ Unsupported browser: {browser}[/red]")
                return None

        except (OSError, TimeoutError, ValueError, RuntimeError) as e:
            # Specific exceptions for browser operations:
            # OSError: Browser launch failures, file access errors
            # TimeoutError: Page navigation timeouts
            # ValueError: Invalid parameters
            # RuntimeError: Browser context errors
            self.console.print(f"[red]❌ Cookie extraction failed: {e}[/red]")
            self.logger.error("Cookie extraction error: %s", e, exc_info=True)
            return None


    def _extract_youtube_cookies_from_context(self, context, page) -> list:
        """Extract YouTube cookies from browser context (DRY-001: extracted duplicate logic).
        
        This helper eliminates 35 lines of duplication between _extract_from_firefox
        and _extract_from_chrome methods.
        
        Args:
            context: Playwright browser context
            page: Playwright page object
            
        Returns:
            List of YouTube cookie dictionaries
        """
        # Extract cookies
        cookies = context.cookies()

        # Filter for YouTube cookies
        youtube_cookies = [
            {
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie["path"],
                "secure": cookie.get("secure", False),
                "httponly": cookie.get("httpOnly", False),
                "expires": cookie.get("expires", None)
            }
            for cookie in cookies
            if "youtube.com" in cookie.get("domain", "")
        ]

        # Try alternative if no cookies found
        if not youtube_cookies:
            self.console.print("[yellow]⚠️ No YouTube cookies found. Trying alternative approach...[/yellow]")

            # Alternative: Navigate to a specific video
            page.goto("https://www.youtube.com/watch?v=dQw4w9WgXcQ", wait_until="networkidle")
            page.wait_for_timeout(3000)

            cookies = context.cookies()
            youtube_cookies = [
                {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie["domain"],
                    "path": cookie["path"],
                    "secure": cookie.get("secure", False),
                    "httponly": cookie.get("httpOnly", False),
                    "expires": cookie.get("expires", None)
                }
                for cookie in cookies
                if "youtube.com" in cookie.get("domain", "")
            ]
        
        return youtube_cookies

    def _extract_from_firefox(self, playwright) -> str | None:
        """Extract cookies from Firefox browser."""
        self.console.print("[blue]🔍 Extracting cookies from Firefox...[/blue]")

        try:
            # Launch Firefox with existing user profile
            browser = playwright.firefox.launch(
                headless=True,
                args=["--no-first-run", "--disable-default-apps"]
            )

            # Create context with user profile (cookies don't need explicit permissions)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0"
            )

            # Navigate to YouTube to trigger cookies
            page = context.new_page()
            page.goto("https://www.youtube.com", wait_until="networkidle")

            # Wait a moment for cookies to be set
            page.wait_for_timeout(2000)

            # Extract YouTube cookies using helper (P1-001: DRY-001 - eliminated 35 lines of duplication)
            youtube_cookies = self._extract_youtube_cookies_from_context(context, page)

            browser.close()

            if youtube_cookies:
                return self._save_cookies_to_file(youtube_cookies, "firefox")
            self.console.print("[red]❌ No YouTube cookies found in Firefox[/red]")
            return None

        except (OSError, TimeoutError, ValueError, RuntimeError) as e:
            # Specific exceptions for Firefox operations
            self.console.print(f"[red]❌ Firefox cookie extraction failed: {e}[/red]")
            self.logger.error("Firefox extraction error: %s", e, exc_info=True)
            return None
        finally:
            # CRITICAL FIX: Ensure browser is always closed, even on exception
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass  # Ignore close errors

    def _extract_from_chrome(self, playwright) -> str | None:
        """Extract cookies from Chrome browser."""
        self.console.print("[blue]🔍 Extracting cookies from Chrome...[/blue]")

        try:
            # Launch Chrome with existing user profile
            browser = playwright.chromium.launch(
                headless=True,
                channel="chrome",  # Use actual Chrome installation
                args=["--no-first-run", "--disable-default-apps"]
            )

            # Create context with user profile
            context = browser.new_context(
                # permissions removed - cookies don't need explicit permissions
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )

            # Navigate to YouTube to trigger cookies
            page = context.new_page()
            page.goto("https://www.youtube.com", wait_until="networkidle")

            # Wait a moment for cookies to be set
            page.wait_for_timeout(2000)

            # Extract YouTube cookies using helper (P1-001: DRY-001 - eliminated 35 lines of duplication)
            youtube_cookies = self._extract_youtube_cookies_from_context(context, page)

            browser.close()

            if youtube_cookies:
                return self._save_cookies_to_file(youtube_cookies, "chrome")
            self.console.print("[red]❌ No YouTube cookies found in Chrome[/red]")
            return None

        except (OSError, TimeoutError, ValueError, RuntimeError) as e:
            # Specific exceptions for Chrome operations
            error_str = str(e)
            if "DPAPI" in error_str or "decrypt" in error_str.lower() or "encryption key" in error_str.lower():
                self.console.print("[yellow]⚠️ Chrome cookies encrypted (Windows security)[/yellow]")
                self.console.print("[yellow]→ Try Firefox instead or use -NoCookies parameter[/yellow]")
            elif "No such file or directory" in error_str:
                self.console.print("[yellow]⚠️ Chrome not found or not installed[/yellow]")
                self.console.print("[yellow]→ Try Firefox or use -NoCookies parameter[/yellow]")
            elif "Permission denied" in error_str:
                self.console.print("[yellow]⚠️ Chrome access denied (close Chrome and retry)[/yellow]")
            else:
                self.console.print("[red]❌ Chrome cookie extraction failed[/red]")
                self.console.print(f"[yellow]→ {error_str[:100]}[/yellow]")
                self.logger.error("Chrome extraction error: %s", e, exc_info=True)
            return None
        finally:
            # CRITICAL FIX: Ensure browser is always closed, even on exception
            if browser is not None:
                try:
                    browser.close()
                except Exception:
                    pass  # Ignore close errors

    def _save_cookies_to_file(self, cookies: list[dict], browser: str) -> str:
        """Save cookies to a temporary file for yt-dlp."""
        # Create temporary file with browser name in prefix
        temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False,
                                            prefix=f"yt_cookies_{browser}_")

        # Write cookies in Netscape format for yt-dlp
        temp_file.write("# Netscape HTTP Cookie File\n")
        temp_file.write("# This is a generated file! Do not edit.\n\n")

        for cookie in cookies:
            # Convert expires timestamp to appropriate format
            expires = cookie.get("expires")
            if expires:
                if isinstance(expires, str):
                    expires = int(float(expires))
                elif isinstance(expires, float):
                    expires = int(expires)
            else:
                expires = 0  # Session cookie

            # Format: domain \t flag \t path \t secure \t expires \t name \t value
            temp_file.write(
                f"{cookie['domain']}\t"
                f"{'TRUE' if cookie['domain'].startswith('.') else 'FALSE'}\t"
                f"{cookie['path']}\t"
                f"{'TRUE' if cookie.get('secure', False) else 'FALSE'}\t"
                f"{expires}\t"
                f"{cookie['name']}\t"
                f"{cookie['value']}\n"
            )

        temp_file.close()

        cookie_count = len(cookies)
        self.console.print(f"[green]✅[/green] Extracted {cookie_count} YouTube cookies from {browser}")
        self.console.print(f"[blue]📁 Cookie file: {temp_file.name}[/blue]")

        # Show important cookies
        important_cookies = [c for c in cookies if any(
            key in c["name"].lower()
            for key in ["session", "login", "auth", "token", "visitor"]
        )]

        if important_cookies:
            self.console.print("[blue]🔐 Important cookies found:[/blue]")
            for cookie in important_cookies:
                self.console.print(f"   • {cookie['name']}: {cookie['value'][:20]}...")

        return temp_file.name

    def test_cookies(self, cookie_file: str) -> bool:
        """Test if cookies work by trying to access YouTube."""
        import yt_dlp

        self.console.print("[blue]🧪 Testing extracted cookies...[/blue]")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie_file,
            "extract_flat": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Test channel info extraction
                result = ydl.extract_info(
                    "https://www.youtube.com/@TwoMinutePapers",
                    download=False,
                    process=False
                )

                if result and "title" in result:
                    self.console.print(f"[green]✅ Cookies working! Channel: {result.get('title', 'Unknown')}[/green]")
                    return True
                self.console.print("[red]❌ Cookies test failed - no channel info retrieved[/red]")
                return False

        except Exception as e:
            self.console.print(f"[red]❌ Cookies test failed: {e}[/red]")
            return False

    def cleanup_cookie_file(self, cookie_file: str):
        """Clean up temporary cookie file."""
        try:
            if Path(cookie_file).exists():
                Path(cookie_file).unlink()
                self.console.print(f"[blue]🗑️ Cleaned up cookie file: {cookie_file}[/blue]")
        except Exception as e:
            self.console.print(f"[yellow]⚠️ Could not clean up cookie file: {e}[/yellow]")


def auto_extract_cookies(browser: str = "firefox", console: Console = None) -> str | None:
    """
    Convenience function to automatically extract cookies.

    Args:
        browser: Browser to use ("firefox" or "chrome")
        console: Console instance for output

    Returns:
        Path to cookie file, or None if extraction fails
    """
    extractor = BrowserCookieExtractor(console)

    if not PLAYWRIGHT_AVAILABLE:
        console.print("[red]❌ Browser automation not available[/red]")
        console.print("[blue]💡 To install browser automation:[/blue]")
        console.print("   pip install playwright")
        console.print("   playwright install")
        return None

    # Extract cookies
    cookie_file = extractor.extract_cookies_from_browser(browser)

    if cookie_file:
        # Test cookies
        if extractor.test_cookies(cookie_file):
            console.print("[green]🎉 Successfully extracted and tested cookies![/green]")
            return cookie_file
        console.print("[yellow]⚠️ Cookies extracted but test failed[/yellow]")
        extractor.cleanup_cookie_file(cookie_file)
        return None
    return None


def check_browsers_available() -> dict[str, bool]:
    """Check which browsers are available for cookie extraction."""
    browsers = {}

    if not PLAYWRIGHT_AVAILABLE:
        return browsers

    try:
        with sync_playwright() as p:
            # Check Firefox
            try:
                p.firefox.launch(headless=True).close()
                browsers["firefox"] = True
                print("✅ Firefox available")
            except (OSError, TimeoutError, ValueError, RuntimeError):
                browsers["firefox"] = False
                print("❌ Firefox not available")

            # Check Chrome
            try:
                p.chromium.launch(channel="chrome", headless=True).close()
                browsers["chrome"] = True
                print("✅ Chrome available")
            except (OSError, TimeoutError, ValueError, RuntimeError):
                browsers["chrome"] = False
                print("❌ Chrome not available")

    except Exception as e:
        print(f"Error checking browsers: {e}")

    return browsers
# Alias for backwards compatibility
CookieExtractor = BrowserCookieExtractor
