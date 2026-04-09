#!/usr/bin/env python3
"""
StopHook_overconfidence_detector.py - Causal Assertion & Catastrophizing Gate

Thin Stop hook wrapper around anti_sycophancy/overconfidence_detector.py.
Catches unverified confident claims:
  - "this explains why..." (causal assertion without evidence)
  - "the system is broken" (catastrophizing)
  - "the root cause is..." (unverified attribution)
  - "definitely/clearly the cause" (overconfident intensifiers)
  - "the hook correctly blocked..." (post-hoc outcome attribution)

Evidence markers in the response (e.g. "logs show", "verified", "[Tier 1]:") exempt
the response from being flagged — this only fires when claims are naked assertions.

Environment:
  OVERCONFIDENCE_DETECTOR_ENABLED  (default: true)
  OVERCONFIDENCE_DETECTOR_MODE     (default: warn, options: warn|block)
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from anti_sycophancy.overconfidence_detector import detect_overconfidence

ENABLED = os.environ.get("OVERCONFIDENCE_DETECTOR_ENABLED", "true").lower() == "true"
MODE = os.environ.get("OVERCONFIDENCE_DETECTOR_MODE", "warn").lower()

# Solution C: Confidence Scope Mismatch — global claims from local evidence (Problem 3)
# Fires when the response makes a global/universal claim but the only evidence
# comes from a single local file read (no Bash, no multi-file traversal).
_GLOBAL_SCOPE_PATTERNS = re.compile(
    r"\b(?:"
    r"working\s+as\s+intended"
    r"|all\s+(?:cases?|instances?|tests?)\s+(?:pass|work|handled?)"
    r"|(?:the\s+)?system\s+(?:works?|is\s+(?:working|correct|fine))"
    r"|every(?:where|thing|one)\s+(?:works?|is\s+(?:handled?|correct))"
    r"|(?:no|zero)\s+(?:issues?|problems?|errors?)\s+(?:found|detected|exist)"
    r"|always\s+(?:works?|handles?|returns?)"
    r")\b",
    re.IGNORECASE,
)

# FIX-005: Remove "Read" from local-only set (RISK:6, prevents false positives)
# Reading code is valid evidence for behavior claims, not zero evidence.
_LOCAL_ONLY_TOOLS: frozenset[str] = frozenset({"Skill"})


# FIX-002: STATUS tag compliance enforcement (RISK:9, prevents false legitimacy)
# Solution D: Enforce that STATUS:INFERRING_FROM_DOCS claims require Bash evidence.
def _check_status_tag_compliance(response: str, tool_events: list[dict[str, Any]]) -> str | None:
    """Flag STATUS:INFERRING_FROM_DOCS without Bash runtime evidence (Solution D)."""
    if "STATUS: INFERRING_FROM_DOCS" not in response:
        return None

    if not tool_events:
        return None

    has_bash = any(e.get("name") == "Bash" for e in tool_events if isinstance(e, dict))

    if not has_bash:
        return (
            "⚠️ **STATUS Tag Violation**: INFERRING_FROM_DOCS requires Bash evidence.\n\n"
            "You attached STATUS:INFERRING_FROM_DOCS but didn't execute Bash for runtime verification.\n\n"
            "Either:\n"
            "- Add Bash verification to confirm runtime behavior, or\n"
            "- Use STATUS:INFERRING_FROM_CODE for Read-only source code analysis"
        )
    return None


def _check_scope_mismatch(response: str, tool_events: list[dict[str, Any]]) -> str | None:
    """Flag global-scope claims backed only by single-file local evidence (Solution C).

    Fires when:
    - Response contains a global/universal scope claim ("working as intended", etc.)
    - All tools used were local reads (Read/Skill), no Bash to run the system
    This is always warn-only (never blocks) — the goal is to prompt hedging.
    """
    if not _GLOBAL_SCOPE_PATTERNS.search(response):
        return None
    if not tool_events:
        return None
    tool_names = {e.get("name", "") for e in tool_events if isinstance(e, dict)}
    # Only flag when tools were used but exclusively local reads — no Bash evidence
    if tool_names and not (tool_names - _LOCAL_ONLY_TOOLS - {""}):
        return (
            "⚠️ **Confidence Scope Mismatch**: Global claim from local evidence.\n\n"
            "You made a system-wide claim but only read individual files (no Bash execution).\n\n"
            "Rewrite scaffold:\n"
            "- Scope the claim: 'In `<file>`, this works because...'\n"
            "- Or run the system: Use Bash to execute and observe actual behavior\n"
            "- Or add uncertainty: 'Based on reading the source, this should work, but not verified'"
        )
    return None


def _get_user_prompt(data: dict[str, Any]) -> str:
    """Get user prompt from multiple sources with fallback priority.

    Priority:
    1. Direct user_prompt field (often provided despite being undocumented)
    2. Last user message from conversation array (documented field per PROTOCOL.md:203)
    3. Empty string (graceful degradation)

    Returns:
        User prompt string, or empty string if unavailable
    """
    # Primary: direct user_prompt field
    prompt = data.get("user_prompt")
    if prompt:
        return str(prompt)

    # Secondary: last user message from conversation array
    conversation = data.get("conversation", [])
    if conversation:
        for msg in reversed(conversation):
            if isinstance(msg, dict) and msg.get("role") == "user":
                return str(msg.get("content", ""))

    # Tertiary: empty string
    return ""


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """In-process validator protocol for Stop_router."""
    if not ENABLED:
        return None

    rca_turn = bool(data.get("rca_turn"))
    response = str(data.get("assistant_response") or data.get("response") or "")
    if not response:
        return None

    user_prompt = _get_user_prompt(data)
    match = detect_overconfidence(response, user_prompt)
    if not match:
        # Solution C: even without overconfidence pattern, check scope mismatch
        tool_events: list[dict[str, Any]] = data.get("tool_events") or []

        # FIX-002: Check STATUS tag compliance (Solution D)
        status_msg = _check_status_tag_compliance(response, tool_events)
        if status_msg:
            # STATUS violations are warn-only (Phase 1 - may escalate to block after monitoring)
            return {"allow": True, "note": status_msg}

        scope_msg = _check_scope_mismatch(response, tool_events)
        if scope_msg:
            # Scope mismatch is always warn-only (never blocks regardless of MODE)
            return {"allow": True, "note": scope_msg}
        return None

    msg = (
        f"⚠️ Overconfident assertion detected: **{match.pattern_type}**\n\n"
        f"Matched: `{match.matched}`\n\n"
        f"Fix: {match.suggestion}\n\n"
        f"Add evidence tier (e.g. `[Tier 1]:`) or reframe as hypothesis to suppress."
    )

    # RCA turns keep this hook advisory to avoid prose-policing loops.
    if MODE == "block" and not rca_turn:
        return {
            "block": True,
            "reason": msg,
            "blocking_hook": "StopHook_overconfidence_detector.py",
        }
    return {"allow": True, "note": msg}
