#!/usr/bin/env python3
"""
StopHook_drift_sentinel.py - TF-IDF Drift Detection for LLM Output
===================================================================

Phase 2 of LLM Behavioral Integrity system.

Detects when generated output semantic similarity drops below 0.75 vs source
documents using TF-IDF cosine similarity (no external APIs, no GPU).
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from cc_diagnostic_logger import log_hook_invocation
from evidence_store import resolve_session_id

try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "drift_sentinel.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.getLogger("drift_sentinel").addHandler(file_handler)
logging.getLogger("drift_sentinel").setLevel(logging.INFO)

logger = structlog.get_logger("drift_sentinel")

DRIFT_SENTINEL_ENABLED = (
    os.environ.get("DRIFT_SENTINEL_ENABLED", "false").lower() == "true"
)
DRIFT_SENTINEL_MODE = os.environ.get("DRIFT_SENTINEL_MODE", "warn").lower()

_MAX_SOURCE_CHARS = 10240  # 10KB per file
_MIN_RESPONSE_CHARS = max(80, int(os.environ.get("DRIFT_SENTINEL_MIN_RESPONSE_CHARS", "240")))
_MIN_SOURCE_COUNT = max(1, int(os.environ.get("DRIFT_SENTINEL_MIN_SOURCE_COUNT", "2")))
_MAX_RESPONSE_CHARS = max(_MIN_RESPONSE_CHARS, int(os.environ.get("DRIFT_SENTINEL_MAX_RESPONSE_CHARS", "4000")))


def load_tool_events(session_id: str, limit: int = 25) -> list[dict[str, Any]]:
    """Compatibility wrapper for recent session evidence."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    return load_scoped_tool_events(
        session_id=session_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


def _load_source_texts(session_id: str) -> list[str]:
    """Load source file content from Read tool events.

    Extracts content from the `command` field of each Read event,
    truncating each file to _MAX_SOURCE_CHARS.
    """
    texts: list[str] = []
    try:
        events = load_tool_events(session_id, limit=25)
    except Exception as e:
        logger.warning("evidence_load_failed", error=str(e))
        return texts

    for event in events:
        name = str(event.get("name", ""))
        if name != "Read":
            continue
        command = str(event.get("command", "") or "")
        if command and len(command) > 0:
            texts.append(command[:_MAX_SOURCE_CHARS])

    return texts


def _should_run_drift_check(response: str, source_texts: list[str]) -> bool:
    """Cheap gating to keep the TF-IDF path off the common Stop path."""
    if len(response.strip()) < _MIN_RESPONSE_CHARS:
        return False
    if len(source_texts) < _MIN_SOURCE_COUNT:
        return False
    return True


def _detect_drift(response: str, source_texts: list[str]) -> dict[str, Any]:
    """Lazy import to avoid paying sklearn startup cost on every Stop invocation."""
    from __lib__.drift_sentinel import detect_drift

    truncated_response = response[:_MAX_RESPONSE_CHARS]
    return detect_drift(truncated_response, source_texts)


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for the drift sentinel hook.

    Args:
        input_data: Hook input data with response and session info

    Returns:
        {"allow": bool, "reason": str | None}
    """
    if not DRIFT_SENTINEL_ENABLED:
        return {"allow": True}

    response = str(input_data.get("response", "") or "")

    # No response → nothing to check
    if not response:
        return {"allow": True}

    session_id = resolve_session_id(input_data.get("session_id", ""))
    if not session_id:
        return {"allow": True}

    source_texts = _load_source_texts(session_id)
    if not source_texts:
        # No Read events → nothing to compare against → fail open
        return {"allow": True}

    if not _should_run_drift_check(response, source_texts):
        return {"allow": True}

    result = _detect_drift(response, source_texts)

    if not result.get("drift_detected", False):
        return {"allow": True}

    # Drift detected
    min_sim = result.get("min_similarity", 0.0)
    reason = (
        f"TF-IDF drift detected: similarity {min_sim:.3f} < 0.75 threshold. "
        f"Response may not be grounded in source documents. "
        f"Re-read documents and ensure claims cite specific content."
    )

    if DRIFT_SENTINEL_MODE == "warn":
        print(f"\n⚠️ DRIFT SENTINEL WARNING\n{reason}\n")
        try:
            log_hook_invocation(
                hook_name="drift_sentinel",
                event_type="drift_check",
                action="warn",
                reason=reason,
            )
        except Exception:
            pass
        return {"allow": True}

    # strict mode
    try:
        log_hook_invocation(
            hook_name="drift_sentinel",
            event_type="drift_check",
            action="block",
            reason=reason,
        )
    except Exception:
        pass
    return {
        "allow": False,
        "reason": reason,
        "blocking_hook": "StopHook_drift_sentinel.py",
    }


if __name__ == "__main__":
    input_text = sys.stdin.read()
    try:
        input_data = json.loads(input_text) if input_text else {}
    except json.JSONDecodeError:
        input_data = {}

    result = run(input_data)
    print(json.dumps(result))
