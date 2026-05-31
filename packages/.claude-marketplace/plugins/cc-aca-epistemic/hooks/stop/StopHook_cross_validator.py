#!/usr/bin/env python3
"""
StopHook_cross_validator.py - Empirical Verification for Fabrication Claims
========================================================================

Task: Fabrication claim detection with evidence verification.

This hook detects fabrication claims (claiming actions occurred when they didn't)
and verifies tool execution evidence to distinguish real errors from fabrications.

Examples:
- Real error: "WebSearch failed with 429" AND WebSearch tool was called → Allow
- Fabrication: "WebSearch failed with 429" but no WebSearch tool → Block

Related: plan-20260317-fabrication-detection.md
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import structlog

HOOKS_DIR = _hooks_dir  # from bootstrap

from claim_patterns import has_action_claim, has_document_claim, has_error_characterization
from cc_diagnostic_logger import log_hook_invocation
from evidence_store import is_file_invalidated, resolve_session_id

try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "cross_validator.log"
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

logging.getLogger("cross_validator").addHandler(file_handler)
logging.getLogger("cross_validator").setLevel(logging.INFO)

logger = structlog.get_logger("cross_validator")

STOP_CROSS_VALIDATOR_ENABLED = (
    os.environ.get("STOP_CROSS_VALIDATOR_ENABLED", "false").lower() == "true"
)
STOP_CROSS_VALIDATOR_MODE = os.environ.get("STOP_CROSS_VALIDATOR_MODE", "warn").lower()


def load_tool_events(session_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Compatibility wrapper for recent session evidence."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    return load_scoped_tool_events(
        session_id=session_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


def verify_document_claim(data: dict[str, Any]) -> dict[str, Any]:
    """
    Verify that document claims have Read tool evidence.

    This function distinguishes between:
    - Valid document claim: Document claim + Read tool evidence → Allow
    - Source fabrication: Document claim + no Read tool → Block

    Args:
        data: Hook input data containing response and session info

    Returns:
        {"allow": bool, "reason": str | None}
    """
    response = str(data.get("response", "") or data.get("assistant_response", ""))

    if not has_document_claim(response):
        return {"allow": True}

    # Document claim detected - verify Read tool execution
    session_id = resolve_session_id(data.get("session_id", ""))

    try:
        events = load_tool_events(session_id, limit=50)
    except Exception as e:
        logger.warning("evidence_load_failed", error=str(e))
        # Fail open on evidence store errors
        return {"allow": True}

    # Check for Read tool execution
    read_executed = any(str(e.get("name", "")) == "Read" for e in events)

    if not read_executed:
        try:
            log_hook_invocation(
                hook_name="cross_validator",
                event_type="document_claim_verification",
                action="block",
                reason="Document claim without Read tool evidence",
            )
        except Exception:
            pass
        return {
            "allow": False,
            "reason": (
                "Document claim detected but no Read tool execution found in evidence. "
                "Claim type: Source fabrication (claiming content from document without reading it). "
                "Required: Read the document first with the Read tool, then cite specific content. "
                "If you haven't read the document, say 'I haven't read that document yet.'"
            ),
            "blocking_hook": "StopHook_cross_validator.py",
        }

    # File invalidation check: ensure no Edit/Write occurred after the Read
    for event in events:
        if str(event.get("name", "")) != "Read":
            continue
        command = str(event.get("command", "") or "")
        if not command:
            continue
        if is_file_invalidated(command):
            try:
                log_hook_invocation(
                    hook_name="cross_validator",
                    event_type="document_claim_verification",
                    action="block",
                    reason="Document claim references invalidated file",
                )
            except Exception:
                pass
            return {
                "allow": False,
                "reason": (
                    f"Document claim references '{command}' which has been modified "
                    "(Edit/Write) after it was read. "
                    "The source file may have changed since your Read. "
                    "Re-read the document to verify your claims are still accurate."
                ),
                "blocking_hook": "StopHook_cross_validator.py",
            }

    return {"allow": True}


def verify_action_claim(data: dict[str, Any]) -> dict[str, Any]:
    """
    Verify that claimed actions actually occurred in tool events.

    This function distinguishes between:
    - Real errors: Action claim + tool execution → Allow
    - Fabrications: Action claim + no tool execution → Block

    Args:
        data: Hook input data containing response and session info

    Returns:
        {"allow": bool, "reason": str | None}
    """
    response = str(data.get("response", "") or data.get("assistant_response", ""))

    if not has_action_claim(response):
        return {"allow": True}

    # Action claim detected - verify tool execution
    session_id = resolve_session_id(data.get("session_id", ""))

    try:
        events = load_tool_events(session_id, limit=50)
    except Exception as e:
        logger.warning("evidence_load_failed", error=str(e))
        # Fail open on evidence store errors to prevent blocking due to system issues
        return {"allow": True}

    # Check for relevant tool execution
    # - WebSearch/WebFetch for research claims
    # - Grep/Bash for search claims
    # - Skill invocation for verification claims
    relevant_tools = {"WebSearch", "WebFetch", "Grep", "Bash", "Skill", "Read"}
    tool_executed = any(str(e.get("name", "")) in relevant_tools for e in events)

    if not tool_executed:
        try:
            log_hook_invocation(
                hook_name="cross_validator",
                event_type="action_claim_verification",
                action="block",
                reason="Action claim without tool execution evidence",
            )
        except Exception:
            pass
        return {
            "allow": False,
            "reason": (
                "Action claim detected but no tool execution found in evidence. "
                "Claim type: Fabrication (action claimed without evidence). "
                "Required: Show tool execution (WebSearch, Grep, Bash, etc.) "
                "or use tentative language (e.g., 'would need to verify')."
            ),
            "blocking_hook": "StopHook_cross_validator.py",
        }

    return {"allow": True}


def verify_error_characterization(data: dict[str, Any]) -> dict[str, Any]:
    """Verify that error-dismissal language has investigation tool evidence."""
    response = str(data.get("response", "") or data.get("assistant_response", ""))

    if not has_error_characterization(response):
        return {"allow": True}

    session_id = resolve_session_id(data.get("session_id", ""))
    try:
        events = load_tool_events(session_id, limit=50)
    except Exception as e:
        logger.warning("evidence_load_failed", error=str(e))
        return {"allow": True}

    investigation_tools = {"Read", "Grep", "Glob", "Bash"}
    investigated = any(str(e.get("name", "")) in investigation_tools for e in events)

    if not investigated:
        try:
            log_hook_invocation(
                hook_name="cross_validator",
                event_type="error_characterization_verification",
                action="block",
                reason="Error characterization without investigation tool evidence",
            )
        except Exception:
            pass
        return {
            "allow": False,
            "reason": (
                "Error characterization detected (transient/benign/no fix needed) "
                "but no investigation tool evidence (Read, Grep, Glob, Bash) found. "
                "Read the error source before characterizing it. "
                "If you haven't investigated, say 'I would need to check the traceback source'."
            ),
            "blocking_hook": "StopHook_cross_validator.py",
        }

    return {"allow": True}


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point for the cross-validation hook.

    Args:
        input_data: Hook input data with response, tools, session info

    Returns:
        {"allow": bool, "reason": str | None}
    """
    if not STOP_CROSS_VALIDATOR_ENABLED:
        return {"allow": True}

    try:
        # First check for document claims (Phase 1 - Citation-Only Ground Truth)
        doc_result = verify_document_claim(input_data)
        if not doc_result["allow"]:
            if STOP_CROSS_VALIDATOR_MODE == "warn":
                reason = doc_result.get("reason", "")
                print(f"\n⚠️ CROSS-VALIDATION WARNING\n{reason}\n")
                return {"allow": True}
            return doc_result

        # Then check for action/fabrication claims
        result = verify_action_claim(input_data)

        if not result["allow"] and STOP_CROSS_VALIDATOR_MODE == "warn":
            # Advisory mode - show warning but allow
            reason = result.get("reason", "")
            print(f"\n⚠️ CROSS-VALIDATION WARNING\n{reason}\n")
            return {"allow": True}

        if not result["allow"]:
            return result

        # Phase 3 - Error characterization without investigation
        error_result = verify_error_characterization(input_data)
        if not error_result["allow"]:
            if STOP_CROSS_VALIDATOR_MODE == "warn":
                reason = error_result.get("reason", "")
                print(f"\n⚠️ CROSS-VALIDATION WARNING\n{reason}\n")
                return {"allow": True}
            return error_result

        return {"allow": True}

    except Exception as e:
        logger.exception("hook_error", error=str(e))
        # Fail open on unexpected errors
        return {"allow": True}


if __name__ == "__main__":
    # Read input from stdin
    input_text = sys.stdin.read()
    try:
        input_data = json.loads(input_text) if input_text else {}
    except json.JSONDecodeError:
        input_data = {}

    result = run(input_data)

    # Output result as JSON
    output = {"decision": "approve" if result.get("allow", True) else "block", "reason": result.get("reason", "")}
    if not result.get("allow", True):
        output = {"decision": "block", "reason": result.get("reason", "")}
    print(json.dumps(_normalize_stdout(output)))
    sys.exit(0 if result["allow"] else 2)
