"""Claude Code status line for model and context pressure.

Claude Code supplies authoritative context-window counters on stdin. Keep this
process fast, side-effect free, and short: status text is advisory telemetry,
not a routing or compaction decision.
"""

from __future__ import annotations

import json
import sys
from typing import Any


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _session_label(payload: dict[str, Any]) -> str:
    """Return an input-bound identity; never infer identity from shared state."""
    session_id = (
        payload.get("session_id")
        or payload.get("sessionId")
        or (payload.get("session") or {}).get("id")
    )
    if not session_id:
        return "sid=?"
    return f"sid={str(session_id)[-8:]}"


def render_status(payload: dict[str, Any]) -> str:
    model = payload.get("model") or {}
    window = payload.get("context_window") or {}
    name = model.get("display_name") or model.get("id") or "model?"
    used = _number(window.get("used_percentage"))
    remaining = _number(window.get("remaining_percentage"))
    size = _number(window.get("context_window_size"))

    if remaining is None and used is not None:
        remaining = max(0.0, 100.0 - used)
    if used is None and remaining is not None:
        used = max(0.0, 100.0 - remaining)

    if used is None:
        context_text = "ctx ?"
    else:
        context_text = f"ctx {used:.0f}% used"
        if size:
            context_text += f"/{size / 1000:.0f}k"

    pressure = ""
    if used is not None:
        if used >= 90:
            pressure = " | COMPACT NOW"
        elif used >= 75:
            pressure = " | compact soon"

    return f"{_session_label(payload)} | {name} | {context_text}{pressure}"


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        print(render_status(payload if isinstance(payload, dict) else {}))
    except Exception:
        print("context status unavailable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
