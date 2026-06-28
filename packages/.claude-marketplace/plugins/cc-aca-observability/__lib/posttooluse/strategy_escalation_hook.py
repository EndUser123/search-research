#!/usr/bin/env python3
from __future__ import annotations

"""
Strategy Escalation Hook - Ring Buffer Implementation.

Detects retry loops by tracking a bounded ring of recent FAILED operations.
Fires when the same (tool, target, operation) hash appears 3+ times in the
last 5 failures -- indicating the agent is stuck retrying the same edit/command.

Design properties:
- Stateless across sessions: ring is bounded to 5 entries; stale data is
  self-diluting (3 new failures of a different type fully evict old entries).
- Multi-terminal safe: different terminals work on different files, producing
  different hashes. Cross-contamination requires identical failed edits, which
  is astronomically unlikely and still produces only a non-blocking warning.
- No TTL needed: the ring never grows; it cannot accumulate stale data.
- Structural failure only: uses the isError flag from Claude Code, not
  substring matching against response text.

Original matcher: ^(Edit|Write|Bash)$
"""

import hashlib
import json
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

from _bootstrap import state_root
STATE_DIR = state_root()
STATE_FILE = STATE_DIR / "strategy_escalation_state.json"

RING_SIZE = 5       # Max failures tracked
LOOP_THRESHOLD = 3  # Same hash N times in ring -> escalate


def _target_hash(tool_name: str, tool_input: dict[str, Any]) -> str:
    """Compute a short hash identifying (tool, target, operation).

    For Edit: (tool, file_path, old_string[:120])  -- old_string is the key
              differentiator; truncated to avoid hashing huge blobs.
    For Write: (tool, file_path)                   -- writes rarely fail;
              target is the file itself.
    For Bash:  (tool, command[:200])               -- first 200 chars captures
              the distinguishing part of most commands.
    """
    if tool_name == "Edit":
        key = (
            tool_name,
            tool_input.get("file_path", ""),
            tool_input.get("old_string", "")[:120],
        )
    elif tool_name == "Write":
        key = (tool_name, tool_input.get("file_path", ""))
    elif tool_name == "Bash":
        key = (tool_name, tool_input.get("command", "")[:200])
    else:
        key = (tool_name, str(sorted(tool_input.items()))[:200])

    return hashlib.md5(str(key).encode()).hexdigest()[:10]


def _is_structural_failure(tool_response: dict[str, Any]) -> bool:
    """Return True only for genuine tool failures.

    Uses the isError flag that Claude Code sets on tool_response when a tool
    actually fails (e.g., Edit old_string not found, Bash non-zero exit).
    Does NOT use substring matching against response text.
    """
    if tool_response.get("isError"):
        return True
    # Secondary: explicit error key with a non-trivial value
    err = tool_response.get("error")
    if err and err is not True and str(err).strip():
        return True
    return False


def _load_ring() -> list[str]:
    """Load the failure ring from state file. Returns [] on any error."""
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            ring = data.get("ring", [])
            if isinstance(ring, list):
                return ring[-RING_SIZE:]
    except Exception:
        pass
    return []


def _save_ring(ring: list[str]) -> None:
    """Persist the failure ring. Silent on error -- hook must never crash."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(
            json.dumps({"ring": ring[-RING_SIZE:]}), encoding="utf-8"
        )
    except OSError:
        pass


class StrategyEscalationHook(PostToolUseHook):
    """Detects retry loops via a bounded ring buffer of failed operations."""

    env_var = "STRATEGY_ESCALATION_ENABLED"
    tool_matcher = {"Edit", "Write", "Bash"}

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        # Only track actual failures -- successes are invisible to this hook.
        if not _is_structural_failure(tool_response):
            return {"passed": True}

        h = _target_hash(tool_name, tool_input)
        ring = _load_ring()
        ring.append(h)
        ring = ring[-RING_SIZE:]

        count = ring.count(h)

        if count >= LOOP_THRESHOLD:
            # Reset ring after firing so the next loop starts fresh.
            _save_ring([])
            return {
                "passed": True,
                "injection": (
                    "STRATEGY ESCALATION REQUIRED: The same edit/command has "
                    f"failed {count} times. Stop retrying the same approach -- "
                    "switch strategy or diagnose the root cause directly."
                ),
            }

        _save_ring(ring)
        return {"passed": True}
