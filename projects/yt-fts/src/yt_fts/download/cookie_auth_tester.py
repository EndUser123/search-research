"""
Cookie Authentication Tester

Provides functional testing for cookie validity by attempting to access
YouTube content. This is more reliable than just checking cookie file existence.

The test works by:
1. Extracting metadata from a known public video
2. If cookies are valid: extraction succeeds
3. If cookies are expired/invalid: yt-dlp returns 403 or sign-in errors

This approach is more robust than testing members-only videos because:
- We don't need to find/maintain a specific members-only video
- Even public videos fail with bad cookies (rate limit/auth errors)
- Works reliably with any stable public video
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Literal

import yt_dlp

# Known public video for testing (Rick Roll - highly unlikely to be deleted)
# This video should always be accessible to logged-in users
_TEST_VIDEO_ID = "dQw4w9WgXcQ"


class CookieTestStatus(Enum):
    """Status codes for cookie authentication tests."""
    VALID = "valid"
    INVALID = "invalid"
    ERROR = "error"
    NO_TEST_VIDEO = "no_test_video"


@dataclass(slots=True)
class CookieTestResult:
    """
    Result of cookie authentication test.

    Attributes:
        status: Test status enum
        message: Human-readable status message
        video_id: Video ID tested
        availability: The availability field from yt-dlp (public, members_only, etc.)
    """
    status: CookieTestStatus
    message: str
    video_id: str
    availability: str | None = None

    def is_valid(self) -> bool:
        """Check if cookies are valid (authentication working)."""
        return self.status == CookieTestStatus.VALID


def test_cookie_authentication(
    video_id: str | None = None,
    cookies_from_browser: Literal["firefox", "chrome"] | None = None,
    timeout: int = 10,
) -> CookieTestResult:
    """
    Test cookie authentication by extracting metadata from a YouTube video.

    This is a functional test - it actually tries to use the cookies to access
    YouTube content. If cookies are valid, extraction succeeds. If cookies are
    expired or invalid, yt-dlp returns authentication errors (403, sign-in).

    Args:
        video_id: Video ID to test. If None, uses a default public video.
        cookies_from_browser: Browser to extract cookies from (firefox or chrome).
        timeout: Request timeout in seconds.

    Returns:
        CookieTestResult with test status and details
    """
    logger = logging.getLogger(__name__)

    # No cookies configured
    if not cookies_from_browser:
        return CookieTestResult(
            status=CookieTestStatus.NO_TEST_VIDEO,
            message="No cookies configured (use --cookies-from-browser)",
            video_id=video_id or _TEST_VIDEO_ID,
        )

    test_video = video_id or _TEST_VIDEO_ID
    test_url = f"https://www.youtube.com/watch?v={test_video}"

    # Configure yt-dlp with cookies
    ydl_opts: dict = {
        "cookiesfrombrowser": (cookies_from_browser,),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": timeout,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)

            if not info:
                return CookieTestResult(
                    status=CookieTestStatus.ERROR,
                    message="Failed to extract video info (empty response)",
                    video_id=test_video,
                )

            availability = info.get("availability", "")
            title = info.get("title", "")

            # Check if we got a valid response with metadata
            # If cookies work, we should get title, availability, etc.
            if title and availability != "members_only":
                return CookieTestResult(
                    status=CookieTestStatus.VALID,
                    message=f"Cookies are working - extracted '{title[:50]}...'",
                    video_id=test_video,
                    availability=availability,
                )

            # Video is still members_only - cookies aren't working
            if availability == "members_only":
                return CookieTestResult(
                    status=CookieTestStatus.INVALID,
                    message="Cookies are expired or invalid (video still members-only)",
                    video_id=test_video,
                    availability=availability,
                )

            # Got info but no title - something is wrong
            return CookieTestResult(
                status=CookieTestStatus.ERROR,
                message="Unexpected response - partial metadata only",
                video_id=test_video,
                availability=availability,
            )

    except Exception as e:
        error_str = str(e)
        logger.debug("Cookie test error: %s", error_str)

        # Detect specific authentication failure indicators
        auth_error_indicators = [
            "HTTP Error 403",
            "403: Forbidden",
            "Sign in",
            "sign in to confirm",
            "authentication",
            "login",
            "cookies",
        ]

        if any(indicator.lower() in error_str.lower() for indicator in auth_error_indicators):
            return CookieTestResult(
                status=CookieTestStatus.INVALID,
                message="Cookies are expired or invalid (authentication failed)",
                video_id=test_video,
            )

        # Video unavailable errors (not an auth problem)
        if "Video unavailable" in error_str or "unavailable" in error_str.lower():
            return CookieTestResult(
                status=CookieTestStatus.ERROR,
                message=f"Test video is unavailable: {error_str}",
                video_id=test_video,
            )

        # Other errors
        return CookieTestResult(
            status=CookieTestStatus.ERROR,
            message=f"Cookie test failed: {e}",
            video_id=test_video,
        )


def get_test_video_id() -> str:
    """Get the default video ID used for cookie testing."""
    return _TEST_VIDEO_ID
