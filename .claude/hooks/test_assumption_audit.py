#!/usr/bin/env python3
"""
Assumption Audit Hook (v0.8.0)
==============================

SIMPLE LOGIC:
- CC responded without observation tools → Soft warning with audit prompt → CC self-evaluates

COMPLIANCE TRACKING (v0.8.0):
- When audit triggers, writes pending state
- Next invocation checks if LLM complied (used tools or marked [UNVERIFIED])
- Logs compliance rate for objective analysis

v0.8.0: Added compliance tracking, switched to soft warning
v0.7.0: Migrated to block_protocol.py (verified working 2025-01-21)
v0.6.0: Original version using exit 2 + stderr
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

ENABLED = os.environ.get("TEST_ASSUMPTION_AUDIT_ENABLED", "true").lower() == "true"
LOG_FILE = Path("P:/.claude/hooks/logs/test_assumption_audit.jsonl")
STATE_DIR = Path("P:/.claude/hooks/state")

# Import terminal detection for isolation (v2.1 - normalized format)
try:
    from __lib.terminal_detection import detect_terminal_id
    TERMINAL_ID = detect_terminal_id()
except ImportError:
    TERMINAL_ID = "fallback_unknown"

# Terminal-scoped pending file (use short hash for filename safety)
import hashlib

TERMINAL_HASH = hashlib.md5(TERMINAL_ID.encode()).hexdigest()[:16]
PENDING_FILE = STATE_DIR / f"pending_assumption_audit_{TERMINAL_HASH}.json"

OBSERVATION_TOOLS = {"Read", "Bash", "Grep", "Glob", "WebFetch", "Search"}


def allow_response(message: str = None) -> None:
    """Allow Claude to stop normally."""
    output = {}
    if message:
        output["systemMessage"] = message
    print(json.dumps(output))
    sys.exit(0)

# Exemptions: MINIMAL - only for latency optimization
# Let CC self-evaluate everything else (we don't pay for that validation)
SAFE_RESPONSE_PATTERNS = [
    # Obvious definitional knowledge (very high confidence signal)
    # Matches: "A mutex is...", "An async function allows...", "A git worktree enables..."
    r"^(?:A|An|The)\s+(?:[\w\-]+\s+)*[\w\-]+\s+(?:is|are|allows?|enables?|provides?)\s+",

    # Announcing verification (avoid blocking when already being explicit)
    r"(?:Let me|I'll|I need to)\s+(?:check|verify|read|search|look|run)\b",

    # Already marked uncertain
    r"\[UNVERIFIED\]",
]

import re

_SAFE_PATTERN_RE = None

def is_safe_response(response: str) -> bool:
    """Check if response is safe (doesn't require verification)."""
    global _SAFE_PATTERN_RE
    if _SAFE_PATTERN_RE is None:
        combined = "|".join(f"({p})" for p in SAFE_RESPONSE_PATTERNS)
        _SAFE_PATTERN_RE = re.compile(combined, re.IGNORECASE | re.MULTILINE)

    # Check patterns
    if _SAFE_PATTERN_RE.search(response.strip()):
        return True

    # Everything else: Let CC self-evaluate via audit prompt
    return False

AUDIT_PROMPT_BRIEF = ""  # Empty = user sees nothing

AUDIT_PROMPT_FULL = """⚠️ ASSUMPTION AUDIT: You responded without using verification tools (Read, Search, Bash).

REQUIRED ACTION:
- If you made factual claims about code, files, or system state → Use Read/Bash to verify NOW
- If you made recommendations based on assumed state → Verify the assumptions first
- If this was general knowledge or definitions → You can proceed

Mark any unverified claims as [UNVERIFIED] if you cannot verify them."""


def log_event(event_type: str, data: dict):
    """Log events for analysis."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "terminal_id": TERMINAL_ID,  # For filtering by terminal
            **data
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# =============================================================================
# COMPLIANCE TRACKING
# =============================================================================

def set_pending_audit(response_snippet: str):
    """Mark that an audit was triggered, pending compliance check."""
    try:
        PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "timestamp": datetime.now().isoformat(),
            "response_snippet": response_snippet[:200],
        }
        with open(PENDING_FILE, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def check_and_clear_pending_audit(tools_used: list[str], response_text: str) -> dict | None:
    """
    Check if there was a pending audit and whether LLM complied.
    
    Returns compliance result dict or None if no pending audit.
    Clears the pending state after checking.
    """
    if not PENDING_FILE.exists():
        return None

    try:
        with open(PENDING_FILE) as f:
            pending = json.load(f)

        # Clear the pending state
        PENDING_FILE.unlink()

        # Check staleness (ignore if > 5 minutes old)
        pending_time = datetime.fromisoformat(pending["timestamp"])
        if datetime.now() - pending_time > timedelta(minutes=5):
            return None

        # Check compliance
        has_observation = any(t in OBSERVATION_TOOLS for t in tools_used)
        has_unverified_marker = "[UNVERIFIED]" in response_text
        complied = has_observation or has_unverified_marker

        result = {
            "pending_timestamp": pending["timestamp"],
            "pending_snippet": pending.get("response_snippet", "")[:100],
            "followup_tools": tools_used,
            "followup_has_observation": has_observation,
            "followup_has_unverified": has_unverified_marker,
            "complied": complied,
        }

        # Log compliance result
        log_event("compliance_check", result)

        return result

    except Exception as e:
        log_event("compliance_error", {"error": str(e)})
        try:
            PENDING_FILE.unlink()
        except Exception:
            pass
        return None


def extract_tools_from_transcript(transcript_path: str) -> list[str]:
    """Extract tool names used in the last assistant turn."""
    tools_used = []
    try:
        content = Path(transcript_path).read_text(encoding="utf-8")

        # Find the LAST assistant entry (iterate in reverse)
        lines = content.strip().split("\n")
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant":
                    # Found last assistant turn, extract tools from it
                    msg = entry.get("message", {})
                    for block in msg.get("content", []):
                        if block.get("type") == "tool_use":
                            tools_used.append(block.get("name", ""))
                    break  # Only process LAST assistant turn
            except json.JSONDecodeError:
                continue
    except Exception as e:
        log_event("extract_error", {"error": str(e)})
    return tools_used


@hook_main
def main():
    import time
    start_time = time.time()

    DEBUG_TEST = os.environ.get("TEST_DEBUG", "0") == "1"

    if not ENABLED:
        if DEBUG_TEST:
            print("Hook disabled", file=sys.stderr)
        allow_response()

    input_data = json.loads(sys.stdin.read())
if __name__ == "__main__":
    main()
