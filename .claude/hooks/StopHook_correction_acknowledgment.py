#!/usr/bin/env python3
"""
StopHook_correction_acknowledgment.py - Correction Acknowledgment Gate
===================================================================

Phase 3 of LLM Behavioral Integrity system.

Detects user corrections (no, wrong, I didn't say) and requires
explicit acknowledgment before the LLM argues back.
"""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib__.correction_detector import check_correction_acknowledge
from cc_diagnostic_logger import log_hook_invocation

LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "correction_acknowledgment.log"
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

logging.getLogger("correction_acknowledgment").addHandler(file_handler)
logging.getLogger("correction_acknowledgment").setLevel(logging.INFO)

logger = structlog.get_logger("correction_acknowledgment")

CORRECTION_GATE_ENABLED = (
    os.environ.get("CORRECTION_GATE_ENABLED", "false").lower() == "true"
)
CORRECTION_GATE_MODE = os.environ.get("CORRECTION_GATE_MODE", "warn").lower()


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for the correction acknowledgment hook.

    Args:
        input_data: Hook input data with user_prompt and response

    Returns:
        {"allow": bool, "reason": str | None}
    """
    if not CORRECTION_GATE_ENABLED:
        return {"allow": True}

    # Extract user message from user_prompt field (NOT user_message)
    user_message = str(input_data.get("user_prompt", "") or "")
    response = str(input_data.get("response", "") or "")

    if not user_message or not response:
        return {"allow": True}

    result = check_correction_acknowledge(user_message, response, proximity_chars=200)

    if result["acknowledged"]:
        try:
            log_hook_invocation(
                hook_name="correction_acknowledgment",
                event_type="correction_check",
                action="allow",
                reason="Correction acknowledged",
            )
        except Exception:
            pass
        return {"allow": True}

    reason = result.get("reason", "User correction detected without acknowledgment.")

    if CORRECTION_GATE_MODE == "warn":
        print(f"\n⚠️ CORRECTION GATE WARNING\n{reason}\n")
        try:
            log_hook_invocation(
                hook_name="correction_acknowledgment",
                event_type="correction_check",
                action="warn",
                reason=reason,
            )
        except Exception:
            pass
        return {"allow": True}

    # strict mode
    try:
        log_hook_invocation(
            hook_name="correction_acknowledgment",
            event_type="correction_check",
            action="block",
            reason=reason,
        )
    except Exception:
        pass
    return {
        "allow": False,
        "reason": reason,
        "blocking_hook": "StopHook_correction_acknowledgment.py",
    }


if __name__ == "__main__":
    input_text = sys.stdin.read()
    try:
        input_data = json.loads(input_text) if input_text else {}
    except json.JSONDecodeError:
        input_data = {}

    result = run(input_data)
    print(json.dumps(result))
