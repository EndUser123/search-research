"""
Cookie extraction validation integration for batch downloads.

This module provides integration hooks to add cookie validation
to the batch downloader before starting downloads.
"""

from typing import TYPE_CHECKING

from rich.console import Console

from .cookie_validator import (
    ValidationResult,
    pre_batch_cookie_warning,
    validate_browser_availability,
)

if TYPE_CHECKING:
    from .batch_downloader import BatchDownloader


def validate_cookies_before_batch(
    console: Console,
    cookies_from_browser: str | None = None,
) -> ValidationResult:
    """
    Validate cookie extraction before starting batch downloads.

    This should be called at the start of BatchDownloader.download_all()
    to warn users about potential cookie extraction issues.

    Args:
        console: Rich Console instance for output
        cookies_from_browser: Browser specified for cookie extraction

    Returns:
        ValidationResult with validation status
    """
    if not cookies_from_browser:
        # No cookies requested - nothing to validate
        return ValidationResult(
            status="success",
            message="Cookie extraction not requested",
            browser=None,
        )

    # Pre-validate cookie extraction
    return pre_batch_cookie_warning(
        console=console,
        browser=cookies_from_browser,
        auto_fallback=True,
    )


def get_best_available_browser(preferred: str = "firefox") -> str:
    """
    Get the best available browser for cookie extraction.

    Args:
        preferred: Preferred browser ("firefox" or "chrome")

    Returns:
        Browser name that should be used
    """
    # Try preferred browser first
    result = validate_browser_availability(preferred)
    if result.is_valid():
        return preferred

    # Try fallback
    fallback = "chrome" if preferred == "firefox" else "firefox"
    result = validate_browser_availability(fallback)
    if result.is_valid():
        return fallback

    # No browser available - return preferred anyway (will fail later)
    return preferred


# Integration function for BatchDownloader
def add_cookie_validation_to_batch(
    batch_downloader: "BatchDownloader"
) -> ValidationResult:
    """
    Add cookie validation to an existing BatchDownloader instance.

    Call this before batch_downloader.download_all().

    Args:
        batch_downloader: BatchDownloader instance

    Returns:
        ValidationResult from cookie validation
    """
    console = batch_downloader.console  # type: ignore[attr-defined]
    browser = batch_downloader.cookies_from_browser  # type: ignore[attr-defined]

    return validate_cookies_before_batch(console, browser)
