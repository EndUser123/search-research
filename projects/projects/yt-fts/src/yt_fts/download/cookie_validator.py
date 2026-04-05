"""
Cookie Extraction Validation Module

Provides validation and verification for browser cookie extraction,
ensuring cookies are valid before attempting downloads.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Literal

from rich.console import Console

try:
    import importlib.util
    _PLAYWRIGHT_AVAILABLE = importlib.util.find_spec("playwright") is not None
except Exception:
    _PLAYWRIGHT_AVAILABLE = False

# Constants for cookie validation (PLR2004)
_IMPORTANT_KEYWORDS = ["session", "login", "auth", "token", "visitor", "sidsid", "pref"]
_NETSCAPE_COOKIE_MIN_FIELDS = 7
_NETSCAPE_COOKIE_NAME_INDEX = 6


class ValidationStatus(Enum):
    """Status codes for cookie extraction validation."""
    SUCCESS = "success"
    NO_PLAYWRIGHT = "no_playwright"
    BROWSER_NOT_AVAILABLE = "browser_not_available"
    EXTRACTION_FAILED = "extraction_failed"
    NO_COOKIES_EXTRACTED = "no_cookies_extracted"
    NO_YOUTUBE_COOKIES = "no_youtube_cookies"


@dataclass
class ValidationResult:
    """
    Result of cookie extraction validation.

    Attributes:
        status: Validation status enum
        message: Human-readable status message
        cookie_count: Number of cookies extracted
        important_cookies: List of important cookie names (session, login, auth, etc.)
        browser: Browser used for extraction
        cookie_file_path: Path to extracted cookie file (if successful)
    """
    status: ValidationStatus
    message: str
    cookie_count: int = 0
    important_cookies: list[str] | None = None
    browser: str | None = None
    cookie_file_path: str | None = None

    def is_valid(self) -> bool:
        """Check if validation indicates successful cookie extraction."""
        return (
            self.status == ValidationStatus.SUCCESS
            and self.cookie_count > 0
            and self.cookie_file_path is not None
        )

    def has_important_cookies(self) -> bool:
        """Check if important cookies (session, login, auth) were extracted."""
        return bool(self.important_cookies)


def validate_browser_availability(browser: Literal["firefox", "chrome"] = "firefox") -> ValidationResult:
    """
    Validate that Playwright and the specified browser are available.

    Args:
        browser: Browser to check availability for

    Returns:
        ValidationResult with status indicating availability
    """
    # Try to import playwright
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return ValidationResult(
            status=ValidationStatus.NO_PLAYWRIGHT,
            message="Playwright not installed. Run: pip install playwright && playwright install",
            browser=browser,
        )

    # Check browser availability
    try:
        with sync_playwright() as p:
            if browser == "firefox":
                p.firefox.launch(headless=True).close()
            elif browser == "chrome":
                p.chromium.launch(channel="chrome", headless=True).close()

        return ValidationResult(
            status=ValidationStatus.SUCCESS,
            message=f"{browser.capitalize()} is available for cookie extraction",
            browser=browser,
        )
    except Exception as e:
        return ValidationResult(
            status=ValidationStatus.BROWSER_NOT_AVAILABLE,
            message=f"{browser.capitalize()} not available: {e}",
            browser=browser,
        )


def warn_if_extraction_would_fail(console: Console, browser: str = "firefox") -> ValidationResult:
    """
    Pre-validate cookie extraction and warn user if it would fail.

    This should be called before starting batch downloads to warn users
    about potential cookie extraction issues.

    Args:
        console: Rich Console instance for output
        browser: Browser to validate

    Returns:
        ValidationResult with status and message
    """
    console.print("[dim]Validating cookie extraction...[/dim]")

    result = validate_browser_availability(browser)

    if result.status == ValidationStatus.NO_PLAYWRIGHT:
        console.print("[yellow]⚠️ Warning: Playwright not available[/yellow]")
        console.print("[dim]→ Cookie extraction will fail. Install with:[/dim]")
        console.print("[dim]   pip install playwright[/dim]")
        console.print("[dim]   playwright install[/dim]")
        console.print("[yellow]→ Downloads will proceed without cookies (may hit rate limits)[/yellow]")
        return result

    if result.status == ValidationStatus.BROWSER_NOT_AVAILABLE:
        console.print(f"[yellow]⚠️ Warning: {browser.capitalize()} not available[/yellow]")
        console.print(f"[dim]→ {result.message}[/dim]")
        console.print("[yellow]→ Cookie extraction will fail. Try:[/dim]")
        console.print("[dim]   1. Install the browser[/dim]")
        console.print("[dim]   2. Use a different browser: --cookies chrome[/dim]")
        console.print("[yellow]→ Downloads will proceed without cookies (may hit rate limits)[/yellow]")
        return result

    # Success - browser is available
    console.print(f"[green]✓ {browser.capitalize()} is available for cookie extraction[/green]")
    return result


def validate_extracted_cookies(
    cookie_file_path: str,
    console: Console | None = None,
) -> ValidationResult:
    """
    Validate that extracted cookies contain necessary YouTube cookies.

    Args:
        cookie_file_path: Path to the extracted cookie file
        console: Optional Console for output

    Returns:
        ValidationResult with validation status
    """
    console = console or Console()
    logger = logging.getLogger(__name__)

    try:
        # Read cookie file
        cookie_path = Path(cookie_file_path)
        if not cookie_path.exists():
            return ValidationResult(
                status=ValidationStatus.EXTRACTION_FAILED,
                message=f"Cookie file not found: {cookie_file_path}",
            )

        with cookie_path.open(encoding="utf-8") as f:
            lines = f.readlines()

        # Parse Netscape cookie file format
        # Format: domain \t flag \t path \t secure \t expires \t name \t value
        cookie_count = 0
        youtube_cookies = 0
        important_cookies = []


        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) >= _NETSCAPE_COOKIE_MIN_FIELDS:
                cookie_count += 1
                domain = parts[0]
                name = parts[_NETSCAPE_COOKIE_NAME_INDEX].lower() if len(parts) > _NETSCAPE_COOKIE_NAME_INDEX else ""

                if "youtube.com" in domain:
                    youtube_cookies += 1
                    if any(keyword in name for keyword in _IMPORTANT_KEYWORDS):
                        important_cookies.append(name)

        if cookie_count == 0:
            return ValidationResult(
                status=ValidationStatus.NO_COOKIES_EXTRACTED,
                message="No cookies found in cookie file",
                cookie_file_path=cookie_file_path,
            )

        if youtube_cookies == 0:
            return ValidationResult(
                status=ValidationStatus.NO_YOUTUBE_COOKIES,
                message=f"Found {cookie_count} cookies, but none for YouTube",
                cookie_count=cookie_count,
                cookie_file_path=cookie_file_path,
            )

        # Success - we have YouTube cookies
        return ValidationResult(
            status=ValidationStatus.SUCCESS,
            message=f"Validated {youtube_cookies} YouTube cookies ({len(important_cookies)} important)",
            cookie_count=cookie_count,
            important_cookies=important_cookies,
            cookie_file_path=cookie_file_path,
        )

    except Exception as e:
        logger.exception("Cookie validation error")
        return ValidationResult(
            status=ValidationStatus.EXTRACTION_FAILED,
            message=f"Cookie validation failed: {e}",
            cookie_file_path=cookie_file_path,
        )


def get_fallback_browser(preferred: str = "firefox") -> str:
    """
    Get a fallback browser if the preferred one is not available.

    Args:
        preferred: Preferred browser ("firefox" or "chrome")

    Returns:
        Browser name that should work, or the preferred if both fail
    """
    browsers = ["firefox", "chrome"]

    # Try preferred first
    result = validate_browser_availability(preferred)
    if result.status == ValidationStatus.SUCCESS:
        return preferred

    # Try fallback
    for browser in browsers:
        if browser != preferred:
            result = validate_browser_availability(browser)
            if result.status == ValidationStatus.SUCCESS:
                return browser

    # No browser available, return preferred anyway
    return preferred


# Convenience function for pre-batch validation
def pre_batch_cookie_warning(
    console: Console,
    browser: str = "firefox",
    auto_fallback: bool = True,
) -> dict[str, ValidationResult]:
    """
    Run comprehensive cookie extraction validation before batch downloads.

    Checks:
    1. Playwright availability
    2. Browser availability
    3. Optionally checks fallback browser

    Args:
        console: Rich Console instance
        browser: Primary browser to check
        auto_fallback: Whether to check fallback browser

    Returns:
        Dict with validation results for each browser checked
    """
    results: dict[str, ValidationResult] = {}

    # Check primary browser
    results[browser] = warn_if_extraction_would_fail(console, browser)

    # Check fallback if enabled and primary failed
    if auto_fallback and not results[browser].is_valid():
        fallback = "chrome" if browser == "firefox" else "firefox"
        console.print(f"[dim]Checking fallback browser ({fallback})...[/dim]")
        results[fallback] = warn_if_extraction_would_fail(console, fallback)

    return results
