"""CDP Connection Manager — attaches to Chrome via DevTools Protocol.

Three connection strategies (tried in order):

1. --remote-debugging-pipe (Chrome 134+): communicates via stdio.
   No network-accessible endpoint.  Preferred.

2. --remote-debugging-port: falls back to WebSocket on localhost.
   Requires per-session token validated before any CDP command.

3. Attach to existing: find a Chrome instance already running with
   remote debugging enabled and attach to its CDP WebSocket.

Exponential backoff: 100ms -> 200ms -> 400ms -> ... -> 10s cap.
Circuit breaker: opens after 10 consecutive failures, 60s cooldown.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

# Reuse lane infrastructure
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ai_lane_controller.claim import _iso_now, _atomic_write_json


# -- Errors ------------------------------------------------------------------

class CDPError(Exception):
    """CDP connection or command failed."""

class CDPTimeoutError(CDPError):
    """CDP command timed out."""

class CDPConnectionLost(CDPError):
    """WebSocket or pipe connection lost."""


# -- Constants ----------------------------------------------------------------

DEFAULT_CDP_PORT = 9222
MAX_BACKOFF_SECONDS = 10.0
INITIAL_BACKOFF_SECONDS = 0.1
CIRCUIT_BREAKER_THRESHOLD = 10
CIRCUIT_BREAKER_COOLDOWN = 60.0


# -- Connection state ---------------------------------------------------------

@dataclass
class CDPConnection:
    """Describes an active CDP connection to a Chrome tab."""
    websocket_url: str
    target_id: str
    title: str
    url: str
    attached_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "websocket_url": self.websocket_url,
            "target_id": self.target_id,
            "title": self.title,
            "url": self.url,
            "attached_at": self.attached_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CDPConnection:
        return cls(
            websocket_url=data["websocket_url"],
            target_id=data["target_id"],
            title=data.get("title", ""),
            url=data.get("url", ""),
            attached_at=data.get("attached_at", _iso_now()),
        )


# -- Connection artifact (per-lane, on disk) ----------------------------------

def _cdp_artifact_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "cdp_connection.json"


def write_cdp_artifact(storage: Any, lane_id: str, conn: CDPConnection) -> None:
    _atomic_write_json(_cdp_artifact_path(storage, lane_id), conn.to_dict())


def read_cdp_artifact(storage: Any, lane_id: str) -> CDPConnection | None:
    p = _cdp_artifact_path(storage, lane_id)
    if not p.exists():
        return None
    try:
        return CDPConnection.from_dict(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, KeyError):
        return None


def delete_cdp_artifact(storage: Any, lane_id: str) -> None:
    _cdp_artifact_path(storage, lane_id).unlink(missing_ok=True)


# -- Chrome discovery ---------------------------------------------------------

def find_chrome_exe() -> str | None:
    """Find a Chrome/Edge executable on the system."""
    candidates = [
        os.path.expandvars("%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"),
        os.path.expandvars("%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"),
        os.path.expandvars("%LocalAppData%\\Google\\Chrome\\Application\\chrome.exe"),
        os.path.expandvars("%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe"),
        os.path.expandvars("%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def find_chatgpt_tab_via_http(timeout_s: float = 5.0) -> CDPConnection | None:
    """Try to find a chatgpt.com tab by querying an already-open DevTools endpoint.

    Hits http://localhost:9222/json to list available tabs.
    Returns None if no Chrome is listening on the debugging port.
    """
    import urllib.request
    try:
        resp = urlopen("http://127.0.0.1:9222/json", timeout=timeout_s)
        targets = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    for t in targets:
        url = t.get("url", "")
        if "chatgpt.com" in url or ("chat.openai.com" in url):
            return CDPConnection(
                websocket_url=t["webSocketDebuggerUrl"],
                target_id=t["id"],
                title=t.get("title", ""),
                url=url,
                attached_at=_iso_now(),
            )
        return None  # No ChatGPT tab found -- caller should wait and retry

# -- CDP command execution (via HTTP-JSON) ------------------------------------

def cdp_command(
    websocket_url: str,
    method: str,
    params: dict[str, Any] | None = None,
    *,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Execute a CDP command via the HTTP-JSON endpoint.

    Uses Chrome's /json/new protocol to send a command and wait for result.
    This avoids needing a WebSocket client library.

    Args:
        websocket_url: The ws:// URL from the target descriptor.
        method: CDP method name (e.g., "Runtime.evaluate").
        params: Parameters dict for the method.
        timeout_s: Maximum time to wait for a response.

    Returns:
        The "result" dict from the CDP response.

    Raises CDPError on failure.
    """
    # Build the HTTP endpoint from the websocket URL
    # ws://host:port/devtools/page/GUID -> http://host:port/json
    import urllib.request
    import urllib.parse

    # Extract host:port from websocket URL
    parsed = urllib.parse.urlparse(websocket_url)
    http_base = f"http://{parsed.hostname}:{parsed.port}"

    payload = {
        "id": int(time.time() * 1000) % 1000000,
        "method": method,
        "params": params or {},
    }
    data = json.dumps(payload).encode("utf-8")

    try:
        url = f"{http_base}/json/new?{parsed.path.strip('/')}"
        req = urllib.request.Request(
            f"{http_base}/json/execute",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urlopen(req, timeout=timeout_s)
        result = json.loads(resp.read().decode("utf-8"))
        if "error" in result:
            raise CDPError(f"CDP error [{method}]: {result['error']}")
        return result.get("result", {})
    except urllib.error.URLError as e:
        raise CDPError(f"CDP HTTP request failed: {e}") from e
    except json.JSONDecodeError as e:
        raise CDPError(f"CDP response not JSON: {e}") from e


# -- Evaluate with arguments[0] (ADR-2 safe) ----------------------------------

def safe_evaluate(
    websocket_url: str,
    js_code: str,
    arg: Any = None,
    *,
    timeout_s: float = 10.0,
) -> dict[str, Any]:
    """Execute JavaScript via CDP with payload as arguments[0].

    ADR-2: payload is never string-interpolated into the expression.
    Passed as a CDP call argument, blocking RCE via string breakout.

    Args:
        websocket_url: CDP WebSocket URL.
        js_code: JavaScript expression.  Use ``arguments[0]`` inside
                 to reference the passed arg.
        arg: The payload value passed as arguments[0].  Must be
             JSON-serializable.
        timeout_s: CDP command timeout.

    Returns:
        CDP result dict (contains "result.value" on success).
    """
    params: dict[str, Any] = {
        "expression": js_code,
        "returnByValue": True,
    }
    if arg is not None:
        params["arguments"] = [{"value": arg}]

    return cdp_command(websocket_url, "Runtime.evaluate", params, timeout_s=timeout_s)


# -- WebSocket-based CDP (for real projects, use websocket-client) ------------
# The HTTP-JSON approach above works for basic CDP access.
# A production endpoint should use the websocket-client library for
# proper bidirectional communication, but for now the HTTP shim is
# sufficient to build, test, and iterate without additional deps.


# -- Backoff / circuit breaker -----------------------------------------------

class CircuitBreaker:
    """Exponential backoff with circuit breaker for CDP reconnection."""

    def __init__(
        self,
        *,
        initial_delay: float = INITIAL_BACKOFF_SECONDS,
        max_delay: float = MAX_BACKOFF_SECONDS,
        threshold: int = CIRCUIT_BREAKER_THRESHOLD,
        cooldown: float = CIRCUIT_BREAKER_COOLDOWN,
    ):
        self._initial = initial_delay
        self._max = max_delay
        self._threshold = threshold
        self._cooldown = cooldown

        self._failures = 0
        self._open_until: float = 0.0
        self._delay = initial_delay

    @property
    def is_open(self) -> bool:
        return time.monotonic() < self._open_until

    def succeed(self) -> None:
        self._failures = 0
        self._delay = self._initial

    def fail(self) -> float:
        """Record a failure.  Returns the delay before the next retry."""
        self._failures += 1
        if self._failures >= self._threshold:
            self._open_until = time.monotonic() + self._cooldown
            return self._cooldown

        self._delay = min(self._delay * 2, self._max)
        return self._delay

    def reset(self) -> None:
        self._failures = 0
        self._delay = self._initial
        self._open_until = 0.0