#!/usr/bin/env python3
"""
Stop hook for Performance Attribution Guardrail.

Detects confident performance/bottleneck/throughput attributions in responses
and verifies that the relevant timing/measurement code was read this session.

No external API calls - uses existing evidence_scope infrastructure.
Fail-open on infrastructure issues.
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
import re
import sys
from pathlib import Path
from typing import Any

# Hooks dir (resolved via plugin hooks_resolver)
HOOKS_DIR = _hooks_dir  # from bootstrap

# ----------------------------------------------------------------------
# Pattern Constants (extensible)
# ----------------------------------------------------------------------

PERF_CLAIM_PATTERNS: list[re.Pattern] = [
    # Dominant factor language
    re.compile(r"\bdominant\s+factor\b", re.IGNORECASE),
    re.compile(r"\bdominates?\b", re.IGNORECASE),
    re.compile(r"\bdominated\s+by\b", re.IGNORECASE),
    re.compile(r"\bbottleneck\b", re.IGNORECASE),
    # Throughput/latency language (when followed by confident attribution)
    re.compile(r"\bthroughput\b.*\b(is|was|dominate|explain|cause)\b", re.IGNORECASE),
    re.compile(r"\blatency\b.*\b(is|was|dominate|explain|cause)\b", re.IGNORECASE),
    # Duration patterns paired with causal claims
    re.compile(r"~\d+\s*s", re.IGNORECASE),  # ~480s
    re.compile(r"\b\d+\s*seconds?\b.*(?:because|due to|caused by|explains|is the reason)", re.IGNORECASE),
    # Specific workflow terms paired with timing
    re.compile(r"yt-dlp.*(?:fetch|download|processing).*~?\d+\s*s", re.IGNORECASE),
    re.compile(r"yt_dlp.*(?:fetch|download|processing).*~?\d+\s*s", re.IGNORECASE),
    re.compile(r"nlm\s+add.*timing", re.IGNORECASE),
    re.compile(r"nlm\s+source\s+add.*wait", re.IGNORECASE),
    re.compile(r"NotebookLM.*timing", re.IGNORECASE),
]

# Terms that indicate hedging (not confident claims)
HEDGE_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bmight\b", re.IGNORECASE),
    re.compile(r"\bcould\b", re.IGNORECASE),
    re.compile(r"\bpossibly\b", re.IGNORECASE),
    re.compile(r"\bprobably\b", re.IGNORECASE),
    re.compile(r"\bperhaps\b", re.IGNORECASE),
    re.compile(r"\bmaybe\b", re.IGNORECASE),
    re.compile(r"\bI\s+suspect\b", re.IGNORECASE),
    re.compile(r"\bappears\s+to\b", re.IGNORECASE),
    re.compile(r"\bseems\s+like\b", re.IGNORECASE),
    re.compile(r"\bestimate\b", re.IGNORECASE),
    re.compile(r"\bhypothesis\b", re.IGNORECASE),
    re.compile(r"\bguess\b", re.IGNORECASE),
    re.compile(r"\baround\b", re.IGNORECASE),
    re.compile(r"\broughly\b", re.IGNORECASE),
    re.compile(r"\bapproximately\b", re.IGNORECASE),
    re.compile(r"\babout\b", re.IGNORECASE),
    # Negation patterns — "no longer dominates", "doesn't dominate", etc.
    re.compile(r"\bno\s+longer\b", re.IGNORECASE),
    re.compile(r"\bdoesn['']t\b", re.IGNORECASE),
    re.compile(r"\bdon['']t\b", re.IGNORECASE),
    re.compile(r"\bwon['']t\b", re.IGNORECASE),
    re.compile(r"\bnot\b", re.IGNORECASE),
    re.compile(r"\bnever\b", re.IGNORECASE),
    # Verification/goal contexts — "confirm X no longer...", "verify X doesn't..."
    re.compile(r"\bconfirm\b", re.IGNORECASE),
    re.compile(r"\bverify\b", re.IGNORECASE),
    re.compile(r"\bcheck\s+that\b", re.IGNORECASE),
    re.compile(r"\bensure\b", re.IGNORECASE),
    re.compile(r"\bshould\s+(?:now|no\s+longer)\b", re.IGNORECASE),
]

# Timing code markers - if these appear in Read/Grep commands, timing code was read
TIMING_CODE_MARKERS: list[str] = [
    "experiment_add_acceptance",
    "add_sources_in_subbatches",
    "elapsed_s",
    "elapsed",
    "time.time",
    "_timing",
    "perf_",
    "benchmark",
]

# ----------------------------------------------------------------------
# Block Message
# ----------------------------------------------------------------------

BLOCK_MESSAGE = """UNVERIFIED PERFORMANCE ATTRIBUTION DETECTED

The response attributes timing/performance results (e.g. "dominant factor", "bottleneck", "~Ns")
without evidence that the timing/measurement code was read this session.

Before attributing bottlenecks or throughput figures:
1. Read the relevant timing/experiment code (e.g. experiment_add_acceptance.py, elapsed_s usage)
2. Verify which step actually dominates the measured elapsed time
3. Then restate the attribution with a citation (file:line)

This prevents confident causal claims that invent a plausible story without checking the code."""

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------

def _detect_perf_claims(text: str) -> bool:
    """Check if text contains confident performance attribution patterns."""
    if not text.strip():
        return False

    # Check each perf pattern
    for pattern in PERF_CLAIM_PATTERNS:
        if pattern.search(text):
            # Found a perf claim - check if it's hedged
            # Get the matching segment for hedge detection
            match = pattern.search(text)
            if match:
                # Get surrounding context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                # Check if context contains hedging
                for hedge in HEDGE_PATTERNS:
                    if hedge.search(context):
                        # Hedged claim - not blocking
                        return False

                # Confident claim - should be blocked if no timing code read
                return True

    return False


def _timing_code_was_read(events: list[dict[str, Any]]) -> bool:
    """Check if any Read or Grep event referenced timing code."""
    for event in events:
        tool_name = event.get("name", "")
        if tool_name not in ("Read", "Grep"):
            continue

        command = str(event.get("command", "")).lower()
        for marker in TIMING_CODE_MARKERS:
            if marker.lower() in command:
                return True

    return False


def _parse_payload() -> dict[str, Any]:
    """Parse Stop hook JSON payload from stdin."""
    try:
        return json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        return {}


def _get_response_text(payload: dict[str, Any]) -> str:
    """Extract response text from payload, checking both key variants."""
    return str(
        payload.get("last_assistant_message")
        or payload.get("response_output")
        or payload.get("assistant_response")
        or ""
    )


def _get_stop_hook_active(payload: dict[str, Any]) -> bool:
    """Get stop_hook_active flag from payload."""
    return bool(payload.get("stop_hook_active", False))


# ----------------------------------------------------------------------
# Main Logic
# ----------------------------------------------------------------------

def run(data: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate response for unverified performance attributions.

    Returns:
        dict with continue (bool) and optionally stopReason (str)
    """
    session_id = str(data.get("session_id", "") or "")
    terminal_id = str(data.get("terminal_id", "") or "")
    response_text = _get_response_text(data)
    stop_hook_active = _get_stop_hook_active(data)

    # Case 1: No perf claims detected -> allow
    if not _detect_perf_claims(response_text):
        return {"continue": True}

    # Case 2+: Perf claims detected - check if timing code was read
    try:
        from evidence_scope import (
            SCOPE_SESSION_FRESH_MUTATION_SAFE,
            load_scoped_tool_events,
        )

        # Retry logic: 3 attempts with 100ms backoff for SQLite contention
        timing_read = False
        for attempt in range(3):
            try:
                events = load_scoped_tool_events(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    scope=SCOPE_SESSION_FRESH_MUTATION_SAFE,
                    limit=500,
                )
                timing_read = _timing_code_was_read(events)
                break  # Success
            except Exception as e:
                if attempt == 2:
                    raise  # Final attempt failed
                import time
                time.sleep(0.1)  # 100ms backoff
    except Exception as e:
        # Fail open: allow on infrastructure issues
        print(f"ERROR: evidence_scope unavailable: {e}", file=sys.stderr)
        return {"continue": True}

    # Case 2: Perf claims + timing code read -> allow
    if timing_read:
        return {"continue": True}

    # Case 3: Perf claims + NO timing code + stop_hook_active=false -> BLOCK
    if not stop_hook_active:
        return {"continue": False, "stopReason": BLOCK_MESSAGE}

    # Case 4: Perf claims + NO timing code + stop_hook_active=true -> allow (loop guard)
    return {"continue": True}


def main() -> int:
    """Entry point for subprocess hook execution."""
    payload = _parse_payload()

    if not payload:
        # Empty payload - allow
        print(json.dumps({"decision": "approve"}))
        return 0

    result = run(payload)
    output = {"decision": "approve" if result.get("allow", True) else "block", "reason": result.get("reason", "")}
    if not result.get("allow", True):
        output = {"decision": "block", "reason": result.get("reason", "")}
    print(json.dumps(_normalize_stdout(output)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())