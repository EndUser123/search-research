"""DOM interaction for ChromeEndpoint — injects into and reads from ChatGPT.

All DOM interaction uses ``arguments[0]`` parameter passing (ADR-2).
Never string-interpolates user content into JavaScript expressions.

DOM selectors are in a version-keyed JSON config (dom_selectors/v1.json).
This file provides the Python API to load and use them.

DOM Fixture Baseline (TEST-3): selectors are tested against fixture HTML
snapshots in tests/endpoints/fixtures/.  A selector change breaks a test
before failing silently at runtime.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from .chrome_endpoint_cdp import safe_evaluate, CDPError


# -- Selector versioning ------------------------------------------------------

SELECTORS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "endpoints" / "dom_selectors"
DEFAULT_SELECTORS_VERSION = "v1"


def load_selectors(version: str = DEFAULT_SELECTORS_VERSION) -> dict[str, Any]:
    """Load DOM selectors for *version* from the selectors directory.

    Returns dict with keys like:
        textarea: CSS selector for the ChatGPT input textarea
        send_button: CSS selector for the send button
        response_container: CSS selector for the response (assistant message) area
        authenticated_marker: CSS selector for an element that only exists when logged in
        error_marker: CSS selector for a block page / CAPTCHA / error state
        streaming_indicator: CSS selector for streaming-in-progress indicator
        empty_state: CSS selector present in the empty state fixture
    """
    path = SELECTORS_DIR / f"{version}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"DOM selectors file not found: {path}. "
            f"Create {path} or check SELECTORS_DIR."
        )
    return json.loads(path.read_text(encoding="utf-8"))


# -- DOM interaction primitives -----------------------------------------------

def inject_text(
    websocket_url: str,
    text: str,
    textarea_selector: str,
) -> dict[str, Any]:
    """Set the ChatGPT textarea value via arguments[0] (ADR-2 safe).

    The expression uses ``arguments[0]`` to receive the payload,
    avoiding string interpolation entirely.
    """
    js = (
        f"(function() {{ "
        f"  const el = document.querySelector('{textarea_selector}'); "
        f"  if (!el) return {{error: 'textarea not found'}}; "
        f"  el.value = arguments[0]; "
        f"  el.dispatchEvent(new Event('input', {{bubbles: true}})); "
        f"  return {{ok: true}}; "
        f"}})()"
    )
    return safe_evaluate(websocket_url, js, arg=text)


def click_send(
    websocket_url: str,
    send_selector: str,
) -> dict[str, Any]:
    """Click the ChatGPT send button via CDP.

    Uses a click via JavaScript since we're already in Runtime.evaluate.
    """
    js = (
        f"(function() {{ "
        f"  const btn = document.querySelector('{send_selector}'); "
        f"  if (!btn) return {{error: 'send button not found'}}; "
        f"  btn.click(); "
        f"  return {{ok: true}}; "
        f"}})()"
    )
    return safe_evaluate(websocket_url, js)


def read_response_text(
    websocket_url: str,
    response_selector: str,
) -> str | None:
    """Read the latest response text from the ChatGPT response container.

    Returns the text content, or None if the container is not found/empty.
    """
    js = (
        f"(function() {{ "
        f"  const el = document.querySelector('{response_selector}'); "
        f"  if (!el) return null; "
        f"  return el.textContent || ''; "
        f"}})()"
    )
    result = safe_evaluate(websocket_url, js)
    value = result.get("result", {}).get("value")
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def is_streaming(
    websocket_url: str,
    streaming_selector: str,
) -> bool:
    """Check if ChatGPT is currently streaming a response.

    Returns True if the streaming indicator element is present.
    """
    js = (
        f"(function() {{ "
        f"  const el = document.querySelector('{streaming_selector}'); "
        f"  return !!el; "
        f"}})()"
    )
    result = safe_evaluate(websocket_url, js)
    return bool(result.get("result", {}).get("value", False))


def wait_for_response(
    websocket_url: str,
    response_selector: str,
    streaming_selector: str,
    *,
    max_wait_s: float = 60.0,
    poll_interval_s: float = 0.5,
) -> str | None:
    """Wait for ChatGPT response to finish, then read it.

    Polls until streaming is done and response text is available.
    Returns the response text, or None on timeout.
    """
    import time

    deadline = time.monotonic() + max_wait_s
    was_streaming = False

    while time.monotonic() < deadline:
        try:
            streaming = is_streaming(websocket_url, streaming_selector)
        except CDPError:
            streaming = False

        if streaming:
            was_streaming = True
            time.sleep(poll_interval_s)
            continue

        if was_streaming:
            # Streaming just finished — give it a moment to settle
            time.sleep(0.3)

        text = read_response_text(websocket_url, response_selector)
        if text:
            return text

        time.sleep(poll_interval_s)

    return None


# -- Health checks -----------------------------------------------------------

def check_authenticated(
    websocket_url: str,
    auth_selector: str,
) -> bool:
    """Check if the ChatGPT page shows an authenticated user.

    Returns True if the authenticated marker element exists.
    """
    js = (
        f"(function() {{ "
        f"  const el = document.querySelector('{auth_selector}'); "
        f"  return !!el; "
        f"}})()"
    )
    result = safe_evaluate(websocket_url, js)
    return bool(result.get("result", {}).get("value", False))


def check_error_state(
    websocket_url: str,
    error_selector: str,
) -> bool:
    """Check if the ChatGPT page is in an error/block/CAPTCHA state.

    Returns True if the error marker element exists.
    """
    js = (
        f"(function() {{ "
        f"  const el = document.querySelector('{error_selector}'); "
        f"  return !!el; "
        f"}})()"
    )
    result = safe_evaluate(websocket_url, js)
    return bool(result.get("result", {}).get("value", False))


def preflight_check(
    websocket_url: str,
    selectors: dict[str, Any],
) -> dict[str, Any]:
    """Run a full pre-flight health check on the ChatGPT page.

    Returns a dict with:
        ok: True if all checks pass
        authenticated: True if logged in
        error_detected: True if CAPTCHA/block page
        textarea_found: True if the textarea exists
    """
    checks = {
        "authenticated": False,
        "error_detected": False,
        "textarea_found": False,
    }

    try:
        checks["authenticated"] = check_authenticated(
            websocket_url, selectors.get("authenticated_marker", "[data-testid='user-avatar']")
        )
    except CDPError:
        checks["authenticated"] = False

    try:
        checks["error_detected"] = check_error_state(
            websocket_url, selectors.get("error_marker", ".cf-error-page")
        )
    except CDPError:
        checks["error_detected"] = False

    try:
        ta_sel = selectors.get("textarea", "textarea")
        result = safe_evaluate(
            websocket_url,
            f"(function() {{ return !!document.querySelector('{ta_sel}'); }})()",
        )
        checks["textarea_found"] = bool(result.get("result", {}).get("value", False))
    except CDPError:
        checks["textarea_found"] = False

    checks["ok"] = (
        checks["authenticated"]
        and not checks["error_detected"]
        and checks["textarea_found"]
    )
    return checks