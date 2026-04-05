import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_mock import MockerFixture

# Import Playwright types needed for 'spec' arguments in mocks
try:
    from playwright.async_api import (
        BrowserContext,
        CDPSession,
        Page,
        Route,
    )
    from playwright.async_api import (
        TimeoutError as PlaywrightTimeoutError,
    )
except ImportError:
    Page = MagicMock()
    Route = MagicMock()
    BrowserContext = MagicMock()
    CDPSession = MagicMock()
    PlaywrightTimeoutError = type("PlaywrightTimeoutError", (Exception,), {})

# Import the modules being tested
from yt_sync.auth_capture import AuthCapturer, _HeaderCapturer


@pytest.fixture
def mock_dependencies(mocker: MockerFixture):
    # --- Patch external libraries ---
    mock_async_playwright_lib = mocker.patch(
        "yt_sync.auth_capture.async_playwright", autospec=True
    )
    mock_Console_class = mocker.patch("yt_sync.auth_capture.Console", autospec=True)
    mock_Panel_class = mocker.patch("yt_sync.auth_capture.Panel", autospec=True)
    mock_Text_class = mocker.patch("yt_sync.auth_capture.Text", autospec=True)
    mock_Path_class = mocker.patch("yt_sync.auth_capture.Path", autospec=True)
    mock_open = mocker.patch("builtins.open", mocker.mock_open())

    # --- Patch standard libraries ---
    mock_asyncio_wait_for = mocker.patch("asyncio.wait_for", new_callable=AsyncMock)

    mock_event_instance = MagicMock(spec=asyncio.Event)
    mock_event_instance.is_set.return_value = False
    mock_event_instance.wait = AsyncMock()
    mocker.patch("asyncio.Event", return_value=mock_event_instance)

    mock_logger_instance = mocker.patch("yt_sync.auth_capture.logger")

    # --- Configure Playwright Mocks ---
    mock_playwright_context_manager = AsyncMock()
    mock_playwright_instance = AsyncMock()
    mock_playwright_context_manager.start.return_value = mock_playwright_instance
    mock_async_playwright_lib.return_value = mock_playwright_context_manager
    mock_playwright_instance.stop = AsyncMock()

    mock_browser = AsyncMock()
    mock_playwright_instance.chromium.launch.return_value = mock_browser

    mock_context = AsyncMock(spec=BrowserContext)
    mock_browser.new_context.return_value = mock_context

    mock_page_instance = AsyncMock(spec=Page)
    mock_context.new_page.return_value = mock_page_instance
    mock_page_instance.context = mock_context

    mock_cdp_session_instance = AsyncMock(spec=CDPSession)
    mock_context.new_cdp_session.return_value = mock_cdp_session_instance
    mock_cdp_session_instance.detach = AsyncMock()

    mock_context.cookies = AsyncMock(return_value=[])

    # --- Configure other mocks ---
    mock_console_instance = MagicMock()
    mock_Console_class.return_value = mock_console_instance

    mock_path_instance = MagicMock(spec=Path)
    mock_path_instance.resolve.return_value = mock_path_instance
    mock_path_instance.__str__.return_value = "/mock/path/cookies.txt"
    mock_Path_class.return_value = mock_path_instance

    return {
        "playwright_instance": mock_playwright_instance,
        "Console_instance": mock_console_instance,
        "logger_instance": mock_logger_instance,
        "asyncio_wait_for": mock_asyncio_wait_for,
        "Path_instance": mock_path_instance,
        "Page_instance": mock_page_instance,
        "CDP_session_instance": mock_cdp_session_instance,
        "Asyncio_Event_instance": mock_event_instance,
        "PlaywrightTimeoutError": PlaywrightTimeoutError,
        "mock_browser": mock_browser,
        "mock_context": mock_context,
        "mock_open": mock_open,
        "Panel_class": mock_Panel_class,
        "Text_class": mock_Text_class,
    }


@pytest.mark.anyio
async def test_header_capturer_init(mock_dependencies):
    capturer = _HeaderCapturer()
    assert capturer.timeout == 300
    assert capturer.headers_found_event is mock_dependencies["Asyncio_Event_instance"]


@pytest.mark.anyio
async def test_check_and_set_event(mock_dependencies):
    capturer = _HeaderCapturer()
    event_mock = mock_dependencies["Asyncio_Event_instance"]
    capturer.headers_found_event = event_mock
    capturer.required_headers = {"Authorization"}

    capturer.captured_headers = {"Authorization"}
    event_mock.is_set.return_value = False
    capturer._check_and_set_event()
    event_mock.is_set.assert_called_once()
    event_mock.set.assert_called_once()


@pytest.mark.anyio
async def test_handle_cdp_request(mock_dependencies):
    capturer = _HeaderCapturer()
    event_mock = mock_dependencies["Asyncio_Event_instance"]
    capturer.headers_found_event = event_mock
    event_mock.is_set.return_value = False

    event = {
        "request": {
            "headers": {
                "authorization": "Bearer token123",
                "x-youtube-identity-token": "abc",
            }
        }
    }
    capturer._handle_cdp_request(event)

    assert capturer.auth_headers["Authorization"] == "Bearer token123"
    assert capturer.auth_headers["x-youtube-identity-token"] == "abc"
    event_mock.set.assert_called_once()


@pytest.mark.anyio
async def test_handle_route(mock_dependencies):
    capturer = _HeaderCapturer()
    event_mock = mock_dependencies["Asyncio_Event_instance"]
    capturer.headers_found_event = event_mock
    event_mock.is_set.return_value = False

    # FIX: Ensure the test only requires the header it provides.
    capturer.required_headers = {"Authorization"}

    mock_route = AsyncMock(spec=Route)
    mock_route.request.all_headers = AsyncMock(
        return_value={"Authorization": "Bearer token123"}
    )

    await capturer._handle_route(mock_route)

    assert capturer.auth_headers["Authorization"] == "Bearer token123"
    event_mock.set.assert_called_once()
    mock_route.continue_.assert_awaited_once()


@pytest.mark.anyio
async def test_run_async_success(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    mock_context = mock_dependencies["mock_context"]
    mock_header_capturer = AsyncMock(spec=_HeaderCapturer)
    mock_header_capturer.wait_for_headers.return_value = {
        "Authorization": "Bearer token123"
    }
    mock_context.cookies.return_value = [
        {"domain": ".youtube.com", "name": "SID", "value": "abc123"}
    ]

    with patch(
        "yt_sync.auth_capture._HeaderCapturer", return_value=mock_header_capturer
    ):
        result = await auth_capturer.run_async()

        assert result is not None
        assert result["http_headers"] == {"Authorization": "Bearer token123"}
        assert result["cookies_file"] == str(mock_dependencies["Path_instance"])
        mock_dependencies["mock_open"].assert_called_once_with(
            mock_dependencies["Path_instance"], "w", encoding="utf-8"
        )


@pytest.mark.anyio
async def test_run_async_timeout(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    mock_page = mock_dependencies["Page_instance"]
    mock_page.wait_for_function.side_effect = mock_dependencies[
        "PlaywrightTimeoutError"
    ]("Timeout!")

    # FIX: Patch with return_value to get a mock instance, not a coroutine.
    mock_header_capturer = AsyncMock(spec=_HeaderCapturer)
    with patch(
        "yt_sync.auth_capture._HeaderCapturer", return_value=mock_header_capturer
    ):
        result = await auth_capturer.run_async()

        assert result is None
        mock_header_capturer.cleanup.assert_awaited_once()
        assert any(
            "Timed out waiting for you to complete the login" in str(c.args[0])
            for c in mock_dependencies["Console_instance"].print.call_args_list
        )


@pytest.mark.anyio
async def test_run_async_exception(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    mock_page = mock_dependencies["Page_instance"]
    mock_logger = mock_dependencies["logger_instance"]

    mock_page.goto.side_effect = Exception("Simulated navigation error")

    # FIX: Patch with return_value to get a mock instance, not a coroutine.
    mock_header_capturer = AsyncMock(spec=_HeaderCapturer)
    with patch(
        "yt_sync.auth_capture._HeaderCapturer", return_value=mock_header_capturer
    ):
        result = await auth_capturer.run_async()

        assert result is None
        mock_header_capturer.cleanup.assert_awaited_once()
        mock_logger.error.assert_called_once()
        assert "An unexpected error occurred" in mock_logger.error.call_args[0][0]


@pytest.mark.anyio
async def test_dependency_error_on_init(mock_dependencies):
    # Simulate dependency import failure
    with patch("yt_sync.auth_capture.async_playwright", None):
        with pytest.raises(ImportError) as exc_info:
            AuthCapturer("https://example.com")
        assert "Required libraries (playwright, rich) are not installed" in str(
            exc_info.value
        )


@pytest.mark.anyio
async def test_cookie_file_verification_success(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    mock_context = mock_dependencies["mock_context"]
    mock_header_capturer = AsyncMock(spec=_HeaderCapturer)
    mock_header_capturer.wait_for_headers.return_value = {
        "Authorization": "Bearer token123"
    }
    mock_context.cookies.return_value = [
        {
            "domain": ".youtube.com",
            "name": "SID",
            "value": "abc123",
            "path": "/",
            "secure": True,
            "expires": 1690000000,
        }
    ]

    mock_file_handle = mock_dependencies["mock_open"]

    with patch(
        "yt_sync.auth_capture._HeaderCapturer", return_value=mock_header_capturer
    ):
        result = await auth_capturer.run_async()

        assert result is not None
        assert "cookies_file" in result
        mock_file_handle.assert_called_once_with(
            mock_dependencies["Path_instance"], "w", encoding="utf-8"
        )
        handle = mock_file_handle()
        handle.write.assert_called_once()
        written_content = handle.write.call_args[0][0]
        assert "# Netscape HTTP Cookie File" in written_content
        assert ".youtube.com\tTRUE\t/\tTRUE\t1690000000\tSID\tabc123" in written_content


@pytest.mark.anyio
async def test_cookie_file_verification_empty_cookies(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    mock_context = mock_dependencies["mock_context"]
    mock_header_capturer = AsyncMock(spec=_HeaderCapturer)
    mock_header_capturer.wait_for_headers.return_value = {
        "Authorization": "Bearer token123"
    }
    mock_context.cookies.return_value = []

    with patch(
        "yt_sync.auth_capture._HeaderCapturer", return_value=mock_header_capturer
    ):
        result = await auth_capturer.run_async()

        assert result is None
        assert any(
            "Failed to capture any cookies" in str(c.args[0])
            for c in mock_dependencies["Console_instance"].print.call_args_list
        )


@pytest.mark.anyio
async def test_convert_cookies_to_netscape_edge_cases(mock_dependencies):
    auth_capturer = AuthCapturer("https://example.com")

    # Test cookies with missing fields, special characters, and no expires
    cookies = [
        {
            "domain": ".youtube.com",
            "name": "SID",
            "value": "abc 123\nspecial\tchars",
            "path": "/",
            "secure": False,
        },
        {
            "domain": ".youtube.com",
            "name": "HSID",
            "value": "",
            "path": "/path",
            "secure": True,
            "expires": -1,
        },
        {"domain": "", "name": "INVALID", "value": "skip_me", "path": "/"},
        {"domain": ".youtube.com", "name": "", "value": "also_skip", "path": "/"},
    ]

    result = auth_capturer._convert_cookies_to_netscape(cookies)

    assert "# Netscape HTTP Cookie File" in result
    assert ".youtube.com\tTRUE\t/\tFALSE\t0\tSID\tabc 123 special chars" in result
    assert ".youtube.com\tTRUE\t/path\tTRUE\t0\tHSID\t" in result
    assert "INVALID" not in result
    assert "also_skip" not in result
