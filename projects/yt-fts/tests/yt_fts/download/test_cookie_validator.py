"""
Unit tests for cookie_validator.py
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_fts.download.cookie_validator import (
    ValidationResult,
    ValidationStatus,
    get_fallback_browser,
    pre_batch_cookie_warning,
    validate_browser_availability,
    validate_extracted_cookies,
    warn_if_extraction_would_fail,
)


class TestValidationResult:
    def test_is_valid_with_success_status_and_cookie_count_and_file_path(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", cookie_count=5, cookie_file_path="/path")
        assert result.is_valid() is True

    def test_is_valid_false_with_no_playwright_status(self):
        result = ValidationResult(status=ValidationStatus.NO_PLAYWRIGHT, message="No", cookie_count=5, cookie_file_path="/path")
        assert result.is_valid() is False

    def test_is_valid_requires_cookie_count_greater_than_zero(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", cookie_count=0, cookie_file_path="/path")
        assert result.is_valid() is False

    def test_is_valid_requires_cookie_file_path(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", cookie_count=5, cookie_file_path=None)
        assert result.is_valid() is False

    def test_has_important_cookies_true_when_list_has_cookies(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", important_cookies=["s"])
        assert result.has_important_cookies() is True

    def test_has_important_cookies_false_when_list_is_empty(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", important_cookies=[])
        assert result.has_important_cookies() is False

    def test_has_important_cookies_false_when_list_is_none(self):
        result = ValidationResult(status=ValidationStatus.SUCCESS, message="Success", important_cookies=None)
        assert result.has_important_cookies() is False


class TestValidateBrowserAvailability:
    @patch("playwright.sync_api.sync_playwright")
    def test_success_when_playwright_and_browser_available(self, mock_sync_playwright):
        mock_ctx = MagicMock()
        mock_browser = MagicMock()
        mock_ctx.firefox.launch.return_value = mock_browser
        mock_sync_playwright.return_value.__enter__.return_value = mock_ctx
        result = validate_browser_availability("firefox")
        assert result.status == ValidationStatus.SUCCESS

    @patch("yt_fts.download.cookie_validator.importlib.util.find_spec", return_value=None)
    def test_no_playwright_module(self, mock_find_spec):
        # When playwright is not available (find_spec returns None),
        # the function should still try to import and fail with NO_PLAYWRIGHT
        # We need to make the actual import fail
        # Save original
        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name.startswith("playwright"):
                msg = "playwright not found"
                raise ImportError(msg)
            return original_import(name, *args, **kwargs)

        try:
            if hasattr(__builtins__, "__import__"):
                __builtins__.__import__ = mock_import
            else:
                __builtins__["__import__"] = mock_import

            result = validate_browser_availability("firefox")
        finally:
            # Restore original import
            if hasattr(__builtins__, "__import__"):
                __builtins__.__import__ = original_import
            else:
                __builtins__["__import__"] = original_import

        assert result.status == ValidationStatus.NO_PLAYWRIGHT


class TestWarnIfExtractionWouldFail:
    def test_success_message_printed(self, mock_console):
        with patch("yt_fts.download.cookie_validator.validate_browser_availability") as m:
            m.return_value = ValidationResult(status=ValidationStatus.SUCCESS, message="OK", browser="firefox")
            result = warn_if_extraction_would_fail(mock_console, "firefox")
            assert result.status == ValidationStatus.SUCCESS


class TestValidateExtractedCookies:
    def test_success_with_youtube_cookies(self, tmp_path):
        f = tmp_path / "t.txt"
        f.write_text(".youtube.com\tTRUE\t/\tTRUE\t1735689600\tSID\ttest\n", encoding="utf-8")
        result = validate_extracted_cookies(str(f), Mock())
        assert result.status == ValidationStatus.SUCCESS

    def test_no_cookies_extracted_empty_file(self, tmp_path):
        f = tmp_path / "e.txt"
        f.write_text("", encoding="utf-8")
        result = validate_extracted_cookies(str(f), Mock())
        assert result.status == ValidationStatus.NO_COOKIES_EXTRACTED

    def test_file_not_found(self, tmp_path):
        result = validate_extracted_cookies(str(tmp_path / "no.txt"), Mock())
        assert result.status == ValidationStatus.EXTRACTION_FAILED


class TestGetFallbackBrowser:
    @patch("yt_fts.download.cookie_validator.validate_browser_availability")
    def test_preferred_browser_available(self, mock_validate):
        mock_validate.return_value = ValidationResult(status=ValidationStatus.SUCCESS, message="OK", browser="firefox")
        assert get_fallback_browser("firefox") == "firefox"

    @patch("yt_fts.download.cookie_validator.validate_browser_availability")
    def test_fallback_when_preferred_unavailable(self, mock_validate):
        mock_validate.side_effect = [
            ValidationResult(status=ValidationStatus.BROWSER_NOT_AVAILABLE, message="No", browser="firefox"),
            ValidationResult(status=ValidationStatus.SUCCESS, message="OK", browser="chrome"),
        ]
        assert get_fallback_browser("firefox") == "chrome"


class TestPreBatchCookieWarning:
    def test_single_browser_check(self, mock_console):
        with patch("yt_fts.download.cookie_validator.warn_if_extraction_would_fail") as m:
            m.return_value = ValidationResult(status=ValidationStatus.SUCCESS, message="OK", browser="firefox")
            result = pre_batch_cookie_warning(mock_console, browser="firefox", auto_fallback=False)
            assert "firefox" in result
            assert len(result) == 1

    def test_auto_fallback_enabled(self, mock_console):
        with patch("yt_fts.download.cookie_validator.warn_if_extraction_would_fail") as m:
            m.side_effect = [
                ValidationResult(status=ValidationStatus.BROWSER_NOT_AVAILABLE, message="No", browser="firefox"),
                ValidationResult(status=ValidationStatus.SUCCESS, message="OK", browser="chrome"),
            ]
            result = pre_batch_cookie_warning(mock_console, browser="firefox", auto_fallback=True)
            assert "firefox" in result
            assert "chrome" in result
            assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
