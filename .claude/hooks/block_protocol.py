#!/usr/bin/env python3
"""
Hook Blocking Protocol v1.0
===========================

Single authoritative source for all Stop hook blocking behavior.

VERIFIED PROTOCOL (2025-01-21):
- {"decision": "block", "reason": "..."} + exit 0 = Claude continues (doesn't stop)
- {} or {"decision": "allow"} + exit 0 = Claude stops normally

Usage:
    from block_protocol import block_response, allow_response
    
    if violation_detected:
        block_response(
            reason="What violated and what Claude should do",
            hook="my_hook_name"
        )
    allow_response()
"""

import json
import logging as _li
import sys
from datetime import datetime
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

BLOCK_LOG = Path("P:/.claude/hooks/logs/block_enforcement.jsonl")


def block_response(reason: str, hook: str, guidance: str = None) -> None:
    """
    Block Claude from stopping - forces continuation.
    
    Args:
        reason: Why blocking + what Claude should do instead (fed to Claude)
        hook: Name of the hook triggering the block (for audit trail)
        guidance: Optional additional guidance (appended to reason)
    
    This function NEVER RETURNS - it exits the process.
    """
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)

    # Build reason with optional guidance
    full_reason = reason
    if guidance:
        full_reason = f"{reason}\n\nGuidance: {guidance}"

    # Official Claude Code Stop hook protocol
    output = {
        "decision": "block",
        "reason": full_reason,
    }

    # Audit trail
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "hook": hook,
        "action": "block",
        "reason": reason[:200],  # Truncate for log readability
    }

    try:
        with open(BLOCK_LOG, "a") as f:
            f.write(json.dumps(audit_entry) + "\n")
    except Exception:
        pass  # Don't fail blocking due to logging issues

    # Output reason to stderr (Stop_router reads this on exit code 2)
    _logger.warning(full_reason)
    sys.exit(2)  # Exit code 2 = BLOCK (per Stop hook protocol)


def allow_response(message: str = None) -> None:
    """
    Allow Claude to stop normally.
    
    Args:
        message: Optional advisory message (shown but doesn't block)
    
    This function NEVER RETURNS - it exits the process.
    """
    output = {}
    if message:
        output["systemMessage"] = message

    print(json.dumps(output))
    sys.exit(0)


def conditional_block(condition: bool, reason: str, hook: str, guidance: str = None) -> None:
    """
    Block if condition is True, otherwise allow.
    
    Convenience function for simple if/else patterns.
    
    Args:
        condition: If True, blocks; if False, allows
        reason: Why blocking (only used if condition is True)
        hook: Hook name for audit trail
        guidance: Optional additional guidance
    """
    if condition:
        block_response(reason=reason, hook=hook, guidance=guidance)
    else:
        allow_response()


# For hooks that want to return result without exiting (e.g., routers)
def make_block_result(reason: str, hook: str = None) -> dict:
    """
    Create a block result dict without exiting.
    
    Use this in routers that aggregate multiple hook results.
    """
    return {
        "decision": "block",
        "reason": reason,
        "_hook": hook,
    }


def make_allow_result(message: str = None) -> dict:
    """
    Create an allow result dict without exiting.
    
    Use this in routers that aggregate multiple hook results.
    """
    result = {}
    if message:
        result["systemMessage"] = message
    return result


def is_block_result(result: dict) -> bool:
    """Check if a result dict represents a block decision."""
    return result.get("decision") == "block"
