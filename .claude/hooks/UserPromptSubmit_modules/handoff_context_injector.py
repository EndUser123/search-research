#!/usr/bin/env python3
"""
UserPromptSubmit Hook: Handoff Context Injector

Automatically injects handoff V2 context (transcript_path, session_id) on every
UserPromptSubmit event when a valid handoff envelope exists.

This enables tools like /chs, /search to reference the previous session's
transcript without requiring explicit user commands.

NOTE: This injector reads from the ACTUAL handoff file location
(P:/.claude/state/handoff/{terminal_id}_handoff.json) which is written by
PreCompact_handoff_capture.py. The file uses terminal_id in the filename
for multi-terminal isolation.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

logger = logging.getLogger(__name__)

# Handoff TTL: 1 hour
HANDOFF_TTL = 3600

# Correct handoff directory (written by PreCompact_handoff_capture.py)
_HANDOFF_DIR = Path("P:/.claude/state/handoff")


def _extract_terminal_id(data: dict) -> str | None:
    """Extract terminal_id from hook data for handoff file lookup.

    Uses terminal_id directly since handoff files use terminal_id in filename
    (e.g., console_{uuid}_handoff.json) for multi-terminal isolation.
    """
    terminal_id = data.get("terminal_id")
    if terminal_id:
        return str(terminal_id)
    return None


def load_handoff_envelope(terminal_id: str) -> dict | None:
    """Load handoff envelope from the actual handoff file.

    Files are stored at P:/.claude/state/handoff/{terminal_id}_handoff.json
    matching the format written by PreCompact_handoff_capture.py.
    """
    # Use terminal_id directly in filename (with console_ prefix preserved)
    state_file = _HANDOFF_DIR / f"{terminal_id}_handoff.json"
    if not state_file.exists():
        logger.debug(f"No handoff file for terminal {terminal_id}: {state_file}")
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        resume = data.get("resume_snapshot", {})
        created_at_raw = resume.get("created_at", 0)
        # Parse ISO 8601 timestamp to epoch
        if isinstance(created_at_raw, str) and created_at_raw:
            from datetime import datetime, timezone
            try:
                dt = datetime.fromisoformat(created_at_raw).replace(tzinfo=timezone.utc)
                created_at = dt.timestamp()
            except (ValueError, OSError):
                created_at = 0
        else:
            created_at = 0
        if time.time() - created_at > HANDOFF_TTL:
            # Only delete if checksum is also invalid (defensive: don't delete
            # valid envelopes just because TTL expired — another path may still
            # need them)
            checksum = data.get("checksum")
            if checksum:
                import hashlib
                resume = data.get("resume_snapshot", {})
                payload = json.dumps(resume, sort_keys=True)
                expected = hashlib.sha256(payload.encode()).hexdigest()[:16]
                if checksum != expected:
                    logger.debug(
                        f"Handoff envelope expired and checksum invalid for {terminal_id}"
                    )
                    state_file.unlink(missing_ok=True)
                    return None
                else:
                    logger.debug(
                        f"Handoff envelope expired but checksum valid for {terminal_id}, keeping"
                    )
                    return None
            else:
                # No checksum to validate — safe to remove expired envelope
                logger.debug(f"Handoff envelope expired (no checksum) for {terminal_id}")
                state_file.unlink(missing_ok=True)
                return None
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load handoff envelope for {terminal_id}: {e}")
        return None


def build_injection_message(envelope: dict) -> str:
    """Build context injection message from handoff envelope."""
    session_id = envelope.get("session_id", "unknown")
    resume = envelope.get("resume_snapshot", {})
    goal = resume.get("goal", "")
    current_task = resume.get("current_task", "")
    active_files = resume.get("active_files", [])
    parts = [
        f"**HANDOFF CONTEXT** (Session: {session_id})",
        "",
    ]
    if goal:
        parts.append(f"**Goal**: {goal}")
    if current_task:
        parts.append(f"**Current Task**: {current_task}")
    if active_files:
        parts.append(f"**Active Files**: {', '.join(active_files)}")
    parts.append("")
    parts.append("This context is from the previous session before compaction.")
    return "\n".join(parts)


@register_hook("handoff_context_injector", priority=5.0)
def handoff_context_injector_hook(context: HookContext) -> HookResult:
    """Inject handoff V2 context on UserPromptSubmit when envelope exists.

    Reads from P:/.claude/state/handoff/{terminal_id}_handoff.json
    which is written by PreCompact_handoff_capture.py and uses terminal_id
    in the filename for correct multi-terminal isolation.
    """
    terminal_id = _extract_terminal_id(context.data)
    if not terminal_id:
        return HookResult.empty()
    envelope = load_handoff_envelope(terminal_id)
    if not envelope:
        return HookResult.empty()
    message = build_injection_message(envelope)
    return HookResult(context=message, tokens=len(message) // 4)
