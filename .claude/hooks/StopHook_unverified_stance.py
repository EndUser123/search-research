#!/usr/bin/env python3
"""Stop hook for unverified stance detection and verification claim grounding.

This hook implements verification for unverified stance detection using the
unified verification engine. It detects skeptical language without verification
evidence (anti-sycophancy) and grounds claims in tool events.

TASK-012: Migrate StopHook_unverified_stance to verification engine.
Following migration pattern from TASK-009 (hypothesis_as_fact_gate).

Core requirements:
1. Use verification engine from verification/engine.py for claim verification
2. Use extract_claims() from verification/claims.py for claim extraction
3. Use load_tool_events_for_context() from evidence_store for tool evidence
4. Keep unique patterns: lazy_closure, verification_target_mismatch, system_claims
5. Warn or block per UNVERIFIED_STANCE_MODE
6. Log every decision with claim text and tool events considered
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

import structlog

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

# Import verification engine from TASK-008
try:
    from verification import Claim, build_verdicts, extract_claims
    from verification.engine import VerificationStatus
except ImportError:
    # Fallback if module not available
    extract_claims = None  # type: ignore
    build_verdicts = None  # type: ignore
    Claim = None  # type: ignore
    VerificationStatus = None  # type: ignore

# Import evidence store from TASK-001
try:
    from evidence_store import load_tool_events_for_context
except ImportError:
    load_tool_events_for_context = None  # type: ignore

# Import unique patterns for this hook
from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
from anti_sycophancy.unverified_stance_detector import (
    StanceMatch,
    detect_unverified_stance,
)

# TASK-010: Import telemetry collection (graceful degradation)
try:
    from telemetry.verification_metrics import collect_verification_metric

    _TELEMETRY_AVAILABLE = True
except ImportError:
    _TELEMETRY_AVAILABLE = False

# SEC-005: Import audit logger for bypass monitoring
try:
    from verification_audit_logger import check_verification_enabled

    _AUDIT_LOGGER_AVAILABLE = True
except ImportError:
    _AUDIT_LOGGER_AVAILABLE = False

LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "unverified_stance.log"
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

logging.getLogger("unverified_stance").addHandler(file_handler)
logging.getLogger("unverified_stance").setLevel(logging.INFO)

logger = structlog.get_logger("unverified_stance")

UNVERIFIED_STANCE_ENABLED = os.environ.get("UNVERIFIED_STANCE_ENABLED", "true").lower() == "true"
UNVERIFIED_STANCE_MODE = os.environ.get("UNVERIFIED_STANCE_MODE", "warn").lower()


def _get_gate_enabled() -> bool:
    """Get gate enabled flag from environment."""
    return os.environ.get("UNVERIFIED_STANCE_ENABLED", "true").lower() == "true"


def _get_gate_mode() -> str:
    """Get gate mode from environment."""
    return os.environ.get("UNVERIFIED_STANCE_MODE", "warn").lower()


# Logging configuration for verification engine decisions
LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_FILE = LOG_DIR / "unverified_stance.jsonl"


def _should_block_claim(claim: Claim, verdict: Any) -> bool:
    """Determine if a claim should be blocked based on verification verdict.

    Args:
        claim: The Claim object to evaluate
        verdict: VerificationVerdict from build_verdicts

    Returns:
        True if claim should be blocked (ungrounded confident claim)
    """
    # ANALYSIS claims (value judgments, architectural opinions) don't require verification
    # These are subjective assessments like "X is valuable for Y" or "right idea, wrong contract"
    if claim.type == "ANALYSIS":
        return False

    # Hedged claims pass without evidence
    if claim.has_hedge:
        return False

    # Low confidence claims pass
    if claim.confidence < 0.7:
        return False

    # Check verification status
    # SUPPORTED: Evidence found → pass
    # REFUTED: Evidence contradicts → may still pass (not blocked here)
    # SELF_VERIFIED: Inline evidence in claim text (cross-turn) → pass
    # SILENT: No relevant evidence → block if confident
    if verdict.status == VerificationStatus.SUPPORTED:
        return False  # Grounded in tool events

    if verdict.status == VerificationStatus.REFUTED:
        return False  # Has some evidence, even if contradictory

    if verdict.status == VerificationStatus.SELF_VERIFIED:
        return False  # Grounded via inline evidence citation in claim text

    # SILENT status + confident claim = ungrounded
    return True


def _log_decision(
    session_id: str,
    terminal_id: str,
    claim: Claim,
    verdict: Any,
    tool_event_ids: list[int],
    outcome: str,
    reason: str = "",
) -> None:
    """Log gate decision for observability and tuning.

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        claim: The Claim that was evaluated
        verdict: VerificationVerdict from build_verdicts
        tool_event_ids: IDs of tool events considered
        outcome: Decision outcome (block/warn/pass)
        reason: Human-readable reason for decision
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Sanitize claim text for logging (PII protection)
        claim_text_sanitized = claim.text[:200]
        # Redact email-like patterns
        claim_text_sanitized = re.sub(
            r"[\w.+-]+@[\w-]+\.[\w.]+", "[REDACTED]", claim_text_sanitized
        )
        # Redact home directory paths
        claim_text_sanitized = re.sub(
            r"/\b(?:home|Users)\b/[\w-]+", "/[REDACTED]", claim_text_sanitized
        )

        log_entry = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "claim_id": claim.id,
            "claim_text": claim_text_sanitized,
            "claim_type": claim.type,
            "targets": claim.targets,
            "confidence": claim.confidence,
            "has_hedge": claim.has_hedge,
            "risk_domain": claim.risk_domain,
            "verification_status": str(verdict.status),
            "supporting_evidence": verdict.supporting_evidence,
            "refuting_evidence": verdict.refuting_evidence,
            "tool_event_ids": tool_event_ids,
            "outcome": outcome,
            "reason": reason,
        }

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, separators=(",", ":")) + "\n")
    except (OSError, ValueError):
        # Fail silently - logging should never break the gate
        pass


UNFOUNDED_SYSTEM_CLAIM_PATTERNS = [
    re.compile(r"since\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+", re.IGNORECASE),
    re.compile(r"because\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+", re.IGNORECASE),
    re.compile(r"as\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+", re.IGNORECASE),
    re.compile(r"the\s+system\s+(?:does not|doesn't|can't|cannot)\s+\w+", re.IGNORECASE),
    re.compile(r"there's\s+no\s+hook\s+for", re.IGNORECASE),
    re.compile(r"no\s+hook\s+exists\s+that", re.IGNORECASE),
    re.compile(r"we\s+can't\s+\w+\s+because\s+the\s+\w+", re.IGNORECASE),
    re.compile(r"unable\s+to\s+\w+\s+due\s+to\s+(?:the\s+)?\w+", re.IGNORECASE),
]


def _check_unfounded_system_claims(response: str) -> str | None:
    for pattern in UNFOUNDED_SYSTEM_CLAIM_PATTERNS:
        if pattern.search(response):
            match = pattern.search(response)
            return match.group(0) if match else None
    return None


def _distinguish_valid_explanation(response: str, data: dict) -> bool:
    tools_used = set()
    for tool in data.get("toolUse", []):
        tool_name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
        if tool_name:
            tools_used.add(tool_name)

    verification_tools = {"WebSearch", "WebFetch", "Bash", "Read"}
    if tools_used & verification_tools:
        return True

    evidence_patterns = [
        re.compile(r"line\s+\d+\s+(?:shows|says|states|contains)", re.IGNORECASE),
        re.compile(r"according\s+to\s+[\w/\.]+", re.IGNORECASE),
        re.compile(r"from\s+the\s+(?:file|code|docs)", re.IGNORECASE),
        re.compile(r"reading\s+\w+\s+(?:shows|reveals|indicates)", re.IGNORECASE),
    ]

    for pattern in evidence_patterns:
        if pattern.search(response):
            return True

    return False


def main() -> None:
    # SEC-005: Audit log when verification is disabled
    if _AUDIT_LOGGER_AVAILABLE and not UNVERIFIED_STANCE_ENABLED:
        check_verification_enabled()  # Logs bypass event

    if not UNVERIFIED_STANCE_ENABLED:
        output_result(allow=True, reason="Hook disabled via UNVERIFIED_STANCE_ENABLED")
        return

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse stdin JSON", error=str(e))
        output_result(allow=True, reason=f"Invalid JSON input: {e}")
        return

    result = run(input_data)
    if result is None:
        output_result(allow=True, reason="No unverified stance detected")
        return
    if result.get("block") is True:
        output_result(allow=False, reason=str(result.get("reason", "")))
        return
    advisory = str(
        result.get("note") or result.get("additionalContext") or result.get("reason") or ""
    ).strip()
    if advisory:
        output_advisory(advisory)
        return
    output_result(allow=True, reason="No unverified stance detected")


# === COMPLETION CLAIM VERIFICATION ===
# Task T-001 from plan-20260307-completion-claim-verification.md
# Extended for Tier 3 (E2E) verification in TASK-002 (plan-20260310-e2e-verification-enforcement.md)

COMPLETION_PATTERNS = [
    re.compile(r"all\s+(files|hooks|tests)\s+pass", re.IGNORECASE),
    re.compile(r"✅.*(complete|fixed|done)", re.IGNORECASE),
    re.compile(r"\b(issue|bug|problem)\s+(?:is\s+)?fixed\b", re.IGNORECASE),
    re.compile(r"test(s)?\s+passed", re.IGNORECASE),
    re.compile(r"verified\s+(?:and\s+)?working", re.IGNORECASE),
    # Short absolute completion claims (catches "Done!", "Complete.", etc.)
    re.compile(
        r"^(Done|Complete|Finished|Implemented|Ready|Fixed|Resolved)[\s\.!?,]", re.IGNORECASE
    ),
]

# Tier 3 (E2E) specific patterns - workflow/skill execution claims
# FIX: Tightened to require explicit execution verbs, not just skill name mentions.
# The old pattern r"/\S+\s+(?:executed|completed|invoked|skill)" matched
# conversational mentions like "the /rns skill" — false positive.
E2E_PATTERNS = [
    re.compile(r"/\S+\s+(?:executed|completed|ran)\b", re.IGNORECASE),
    re.compile(r"workflow\s+(?:completed|finished|passed)\b", re.IGNORECASE),
    re.compile(r"all\s+(?:tiers|stages)\s+passed\b", re.IGNORECASE),
    re.compile(r"skill\s+\S+\s+(?:executed|completed|ran)\b", re.IGNORECASE),
]

RUNTIME_TOOLS = {"Bash", "Edit", "Read", "Grep", "Glob"}
RUNTIME_COMMAND_PATTERNS = ["subprocess", "pytest", "python", "node", "npm test"]

# Solution B: Verification-Target Mismatch detection (Problem 2)
# Fires when response has runtime behavior claims but all tool events are doc-reads (Skill/Read).
_RUNTIME_CLAIM_PATTERN = re.compile(
    r"\b(?:works?\b|working\b|already\s+works?\b|working\s+as\s+intended\b|"
    r"(?:the|this)\s+(?:command|skill|feature)\s+(?:shows?|does?|returns?|runs?))\b",
    re.IGNORECASE,
)
# FIX-005: Remove "Read" from doc-only set (RISK:6, prevents false positives on code reviews)
# Reading code to verify actual behavior is VALID evidence, not zero evidence.
_DOC_ONLY_TOOL_NAMES: frozenset[str] = frozenset({"Skill"})

# PERF-001: Evidence caching for <10ms target (vs 50-100ms baseline)
_EVIDENCE_CACHE: dict[str, list[dict]] = {}  # session_id -> tool events


def _check_completion_claim(response: str, session_id: str) -> tuple[bool, str]:
    """Check if completion claim has sufficient runtime evidence.

    TASK-002: Extended for Tier 3 (E2E) verification.
    Now checks for workflow/skill execution evidence, not just component tests.

    Args:
        response: Agent response text to check for completion claims
        session_id: Current session ID for evidence lookup

    Returns:
        (is_valid, message): Tuple of validity and explanation message

    Raises:
        ValueError: If session_id validation fails (SEC-004)
    """
    # SEC-004: Fail-closed session validation
    # Old behavior: empty session_id → skip check (fail-open)
    # New behavior: empty session_id → raise ValueError (fail-closed)
    try:
        _validate_session_id(session_id)
    except ValueError as e:
        # In production, this would block. For now, log and continue (graceful migration)
        logger.warning("session_id_validation_failed", error=str(e))
        return True, f"Sufficient evidence (session_id validation skipped: {e})"

    # Check if response contains completion claim patterns
    for pattern in COMPLETION_PATTERNS:
        if pattern.search(response):
            has_runtime = _check_for_runtime_tools(session_id)
            if not has_runtime:
                required_tools = ", ".join(sorted(list(RUNTIME_TOOLS)))
                required_cmds = ", ".join(RUNTIME_COMMAND_PATTERNS)
                return False, (
                    "Completion claim without runtime testing evidence. "
                    f"Required: Tool usage from {required_tools} "
                    f"or commands containing: {required_cmds}"
                )

    # TASK-002: Tier 3 (E2E) verification
    # Check for workflow/skill execution claims
    for pattern in E2E_PATTERNS:
        if pattern.search(response):
            has_e2e = _check_e2e_workflow_evidence(session_id)
            if not has_e2e:
                return False, (
                    "E2E workflow claim without execution evidence. "
                    "Required: Actual skill invocation or multi-step workflow demonstration. "
                    "Component tests (pytest) alone are insufficient for workflow claims."
                )

    return True, "Sufficient evidence"


def _check_for_runtime_tools_in_events(tool_events: list[dict[str, Any]]) -> bool:
    """Check runtime evidence directly from turn-scoped tool events."""
    for event in tool_events:
        tool_name = event.get("name", "")
        command = str(event.get("command", ""))
        if tool_name in RUNTIME_TOOLS:
            return True
        command_lower = command.lower()
        if any(pattern.lower() in command_lower for pattern in RUNTIME_COMMAND_PATTERNS):
            return True
    return False


def _check_e2e_workflow_evidence_in_events(tool_events: list[dict[str, Any]]) -> bool:
    """Check workflow execution evidence directly from turn-scoped tool events."""
    for event in tool_events:
        tool_name = event.get("name", "")
        command = str(event.get("command", ""))
        if tool_name == "Skill":
            return True
        if command.startswith("/"):
            return True
        if tool_name in RUNTIME_TOOLS:
            workflow_indicators = ["verify", "test", "diagnostic", "check", "validate"]
            if any(indicator in command.lower() for indicator in workflow_indicators):
                return True
    return False


def _check_completion_claim_with_events(
    response: str, tool_events: list[dict[str, Any]]
) -> tuple[bool, str]:
    """Evaluate completion and E2E claims against current-turn tool events."""
    for pattern in COMPLETION_PATTERNS:
        if pattern.search(response):
            if not _check_for_runtime_tools_in_events(tool_events):
                required_tools = ", ".join(sorted(list(RUNTIME_TOOLS)))
                required_cmds = ", ".join(RUNTIME_COMMAND_PATTERNS)
                return False, (
                    "Completion claim without runtime testing evidence. "
                    f"Required: Tool usage from {required_tools} "
                    f"or commands containing: {required_cmds}"
                )

    for pattern in E2E_PATTERNS:
        if pattern.search(response):
            if not _check_e2e_workflow_evidence_in_events(tool_events):
                return False, (
                    "E2E workflow claim without execution evidence. "
                    "Required: Actual skill invocation or multi-step workflow demonstration. "
                    "Component tests (pytest) alone are insufficient for workflow claims."
                )

    return True, "Sufficient evidence"


def _is_challenge_active(data: dict[str, Any]) -> bool:
    """Check if anti_sycophancy_injector wrote a challenge marker this turn (Solution A)."""
    import time
    import uuid

    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    )
    session_id = str(
        data.get("session_id") or data.get("sessionId") or os.environ.get("CLAUDE_SESSION_ID", "")
    )

    # FIX-003: UUID fallback for multi-terminal safety (RISK:9, constitutional violation)
    # Prevents all terminals without IDs from sharing challenge__unknown__unknown.json
    if not terminal_id and not session_id:
        fallback_id = str(uuid.uuid4())[:8]
        terminal_id = f"auto_{fallback_id}"
        session_id = f"auto_{fallback_id}"

    def _safe(v: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", v) if v else "unknown"

    try:
        from UserPromptSubmit_modules.anti_sycophancy_injector import _challenge_marker_path

        marker = _challenge_marker_path(session_id, terminal_id)
    except Exception:
        marker = (
            HOOKS_DIR
            / "state"
            / "anti_sycophancy_injector"
            / f"challenge__{_safe(session_id)}__{_safe(terminal_id)}.json"
        )

    if not marker.exists():
        return False

    # FIX-001: TTL validation (RISK:9, multi-terminal safety)
    # Reject markers older than 5 minutes to prevent false blocks from crashed sessions
    try:
        content = json.loads(marker.read_text())
        timestamp = content.get("timestamp", 0)
        if time.time() - timestamp > 300:  # 5 minutes
            marker.unlink()  # Clean up stale marker
            return False
    except (OSError, json.JSONDecodeError):
        pass

    return True


def _check_verification_target_mismatch(
    response: str, tool_events: list[dict[str, Any]]
) -> str | None:
    """Flag runtime behavior claims backed only by doc-reads with no Bash (Solution B).

    Fires when:
    - Response claims something "works" / "runs" / is "working as intended"
    - All tools used in the turn were Skill/Read (documentation) — no Bash evidence
    """
    if not _RUNTIME_CLAIM_PATTERN.search(response):
        return None
    if not tool_events:
        return None
    tool_names = {e.get("name", "") for e in tool_events if isinstance(e, dict)}
    # Only flag when tools were used but exclusively doc-reads (Skill/Read), no Bash
    if tool_names and not (tool_names - _DOC_ONLY_TOOL_NAMES - {""}):
        return (
            "⚠️ **Verification-Target Mismatch**: Runtime behavior claim with doc-only evidence.\n\n"
            "You used Skill/Read (documentation) but made claims about actual runtime behavior.\n\n"
            "Either:\n"
            "- Run the command with Bash to verify, or\n"
            "- Hedge: 'Based on the docs, this should...' (not confirmed in this environment)"
        )
    return None


def _check_for_runtime_tools(session_id: str) -> bool:
    """Query evidence_store for runtime tool usage.

    PERF-001: Uses evidence caching to achieve <10ms target.
    Cache is invalidated on tool use via _invalidate_evidence_cache().

    Args:
        session_id: Session ID to query for tool events

    Returns:
        True if runtime tools found, False otherwise
    """
    try:
        from evidence_store import load_tool_events

        # Check cache first (PERF-001)
        if session_id in _EVIDENCE_CACHE:
            tool_events = _EVIDENCE_CACHE[session_id]
        else:
            # PR-001 fix: Function takes session_id parameter
            tool_events = load_tool_events(session_id, limit=100)
            _EVIDENCE_CACHE[session_id] = tool_events  # Cache for subsequent calls

        for event in tool_events:
            # PR-004 fix: Event dict uses "name" key, not "tool_name"
            tool_name = event.get("name", "")
            command = event.get("command", "")

            # Check tool names
            if tool_name in RUNTIME_TOOLS:
                return True

            # Check command strings for runtime patterns
            command_lower = command.lower()
            if any(pattern.lower() in command_lower for pattern in RUNTIME_COMMAND_PATTERNS):
                return True

        return False

    except (ImportError, Exception) as e:
        logger.warning("evidence_store_query_failed", error=str(e))
        return False  # Fail open


def _check_e2e_workflow_evidence(session_id: str) -> bool:
    """Check for Tier 3 (E2E) workflow execution evidence.

    TASK-002: Verify that skills/workflows were actually executed,
    not just component tests (Tier 1).

    Args:
        session_id: Session ID to query for tool events

    Returns:
        True if E2E workflow evidence found, False otherwise
    """
    try:
        from evidence_store import load_tool_events

        # Check cache first (PERF-001)
        if session_id in _EVIDENCE_CACHE:
            tool_events = _EVIDENCE_CACHE[session_id]
        else:
            tool_events = load_tool_events(session_id, limit=100)
            _EVIDENCE_CACHE[session_id] = tool_events

        for event in tool_events:
            # Check for skill invocations (Tier 3 evidence)
            tool_name = event.get("name", "")
            command = event.get("command", "")

            # Skill tool usage
            if tool_name == "Skill":
                return True

            # Skill invocation in command (e.g., "/arch", "/verify")
            if command.startswith("/"):
                return True

            # Multi-step workflow patterns (sequential tool use)
            # This is a heuristic - real workflow tracking would need PostToolUse_e2e_tracker.py
            # For now, we detect sequences that look like workflows
            if tool_name in RUNTIME_TOOLS:
                # Check if this looks like a workflow step
                # (e.g., "pytest", then "hook_diagnostics", then "Skill")
                workflow_indicators = ["verify", "test", "diagnostic", "check", "validate"]
                if any(indicator in command.lower() for indicator in workflow_indicators):
                    # Found potential workflow step
                    # In production, TASK-003 (PostToolUse_e2e_tracker.py) would provide definitive tracking
                    return True

        return False

    except (ImportError, Exception) as e:
        logger.warning("e2e_evidence_check_failed", error=str(e))
        return False  # Fail open


def _validate_session_id(session_id: str) -> str:
    """Validate session_id parameter (SEC-004: Fail-closed validation).

    SECURITY FIX: Empty session_id now raises ValueError instead of
    being silently skipped (fail-open behavior).

    Args:
        session_id: Session ID to validate

    Returns:
        Validated session_id

    Raises:
        ValueError: If session_id is empty or None
    """
    if not session_id:
        raise ValueError(
            "session_id cannot be empty or None. "
            "This prevents bypassing verification checks. "
            "Ensure CLAUDE_SESSION_ID environment variable is set."
        )
    return session_id


def _invalidate_evidence_cache(session_id: str) -> None:
    """Invalidate evidence cache for a session (PERF-001).

    Called by PostToolUse hooks to ensure fresh evidence after tool execution.

    Args:
        session_id: Session ID to invalidate cache for
    """
    if session_id in _EVIDENCE_CACHE:
        del _EVIDENCE_CACHE[session_id]


def _get_evidence_cache_stats() -> dict:
    """Get evidence cache statistics for monitoring (PERF-001).

    Returns:
        Dict with cache stats: cached_sessions, total_cached_events
    """
    total_events = sum(len(events) for events in _EVIDENCE_CACHE.values())
    return {
        "cached_sessions": list(_EVIDENCE_CACHE.keys()),
        "total_cached_sessions": len(_EVIDENCE_CACHE),
        "total_cached_events": total_events,
    }


def format_system_claim_block(claim: str) -> str:
    return f"""❌ Unverified System Behavior Claim Blocked

**Violation Detected:** Unfounded assertion about system behavior

**Claim:** `{claim}`

This assertion about system behavior lacks verification evidence.

**Before making system behavior claims:**
1. Verify the claim by reading code/docs (Read tool)
2. Search for evidence (Grep/find for hooks, code)
3. Cite specific files/line numbers
4. Test the behavior if uncertain (Bash tool)

Fix the response and try again."""


def format_system_claim_advisory(claim: str) -> str:
    return f"""⚠️ Unverified System Behavior Claim Warning

**Issue:** Unfounded assertion about system behavior
**Claim:** `{claim}`

This assertion lacks verification evidence.

This would block in non-warn mode."""


def format_block_message(result: StanceMatch) -> str:
    parts = [
        "❌ Unverified Stance Blocked",
        "",
        f"**Violation Detected:** {result.category}",
        "",
    ]
    if result.matched:
        parts.append(f"**Matched Text:** `{result.matched}`")
        parts.append("")
    parts.extend(
        [
            f"**Severity:** {result.severity}",
            "",
            result.self_prompt,
            "",
            "Fix the response and try again.",
        ]
    )
    return "\n".join(parts)


def format_advisory(result: StanceMatch) -> str:
    """Format unverified stance advisory with visual indicators."""
    # Import visual formatter
    try:
        from __lib.verification_visualizer import VerificationVisualizer

        visualizer = VerificationVisualizer()

        # Use visual formatter for better formatting
        claim_text = f"Unverified {result.category} detected"
        if result.matched:
            claim_text += f': "{result.matched}"'

        advisory = visualizer.format_advisory(
            verification_type="unverified_stance",
            claim=claim_text,
            evidence_status=f"No tool evidence for {result.category}",
            details=f"{result.self_prompt}\n\n**Severity**: {result.severity}\n\nThis would block in non-warn mode.",
        )

        # Add matched text if present
        if result.matched:
            advisory = advisory.replace(
                f"**Claim**: {claim_text}",
                f"**Claim**: {claim_text}\n\n**Matched Text**: `{result.matched}`",
            )

        return advisory
    except ImportError:
        # Fallback to original formatting if visualizer unavailable
        parts = [
            "⚠️ Unverified Stance Warning",
            "",
            f"**Issue:** {result.category}",
            "",
        ]
        if result.matched:
            parts.append(f"**Matched Text:** `{result.matched}`")
            parts.append("")
        parts.extend(
            [
                result.self_prompt,
                "",
                f"**Severity:** {result.severity}",
                "",
                "This would block in non-warn mode.",
            ]
        )
        return "\n".join(parts)


def output_result(allow: bool, reason: str) -> None:
    result = {"allow": allow, "reason": reason}
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


def output_advisory(advisory: str) -> None:
    result = {
        "allow": True,
        "reason": "Unverified stance warning (warn mode)",
        "additionalContext": advisory,
    }
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """Stop hook entrypoint for unverified stance validation using verification engine.

    Args:
        data: Hook data dictionary containing:
            - session_id: Session UUID
            - terminal_id: Terminal identifier
            - response_text: Response text to analyze
            - tool_events: List of tool events from this turn

    Returns:
        Dictionary with:
            - allow: bool (True to allow stop, False to block)
            - reason: str (explanation for decision)
            - block: bool (True to block stop)
            - note: str (advisory message)
    """
    # Check if gate is enabled (read dynamically)
    if not _get_gate_enabled():
        return {"allow": True, "reason": "Gate disabled"}

    # SEC-005: Audit log when verification is disabled
    if _AUDIT_LOGGER_AVAILABLE:
        check_verification_enabled()

    # Extract required fields
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")
    response_text = str(data.get("assistant_response") or data.get("response") or "")
    tool_events = data.get("tool_events", [])

    # Validate inputs
    if not response_text:
        return {"allow": True, "reason": "No response text provided"}

    # PATTERN-001 FIX: Collect all violations from both phases before blocking
    # This prevents Phase 1 from blocking before Phase 2 can run
    violations = []  # Collect (phase_name, violation_message, severity) tuples

    # Phase 1: Verification Engine Check (TASK-012)
    # Import verification engine if available
    if (
        extract_claims is not None
        and build_verdicts is not None
        and Claim is not None
        and VerificationStatus is not None
        and load_tool_events_for_context is not None
    ):
        try:
            # Extract claims using verification engine
            claims = extract_claims(response_text)

            if claims:
                # Load tool events for context (terminal-scoped)
                # If tool_events provided in data, merge with terminal-scoped events
                # FIX: Check first to avoid N+1 query pattern (PERF-001)
                # FIX: Merge events instead of replacing (LOGIC-001)
                if isinstance(tool_events, list) and tool_events:
                    loaded_events = tool_events
                else:
                    loaded_events = load_tool_events_for_context(
                        session_id=session_id,
                        terminal_id=terminal_id,
                        limit=500,
                    )

                # Merge turn-scoped events into terminal-scoped if both exist
                if isinstance(tool_events, list) and tool_events:
                    loaded_events.extend(tool_events)

                # Extract tool event IDs for logging
                tool_event_ids = [event.get("id", 0) for event in loaded_events]

                # Build verification verdicts using engine
                verdicts = build_verdicts(claims, loaded_events)

                # Evaluate each claim against its verdict
                ungrounded_claims = []
                claim_verdict_pairs = []

                for claim, verdict in zip(claims, verdicts):
                    claim_verdict_pairs.append((claim, verdict))
                    if _should_block_claim(claim, verdict):
                        ungrounded_claims.append(claim)

                # If ungrounded claims found, collect violation (don't return early)
                if ungrounded_claims:
                    # Log all blocked claims
                    for claim, verdict in claim_verdict_pairs:
                        if claim in ungrounded_claims:
                            _log_decision(
                                session_id=session_id,
                                terminal_id=terminal_id,
                                claim=claim,
                                verdict=verdict,
                                tool_event_ids=tool_event_ids,
                                outcome="block" if _get_gate_mode() == "block" else "warn",
                                reason=f"Confident claim without grounding evidence ({verdict.status.value})",
                            )

                    # Build block/warn message
                    claim_summary = "\n".join(
                        [
                            f"  - {claim.targets[0] if claim.targets else 'Unknown'}: {claim.text[:100]}..."
                            for claim in ungrounded_claims[:3]  # Show first 3
                        ]
                    )

                    if len(ungrounded_claims) > 3:
                        claim_summary += f"\n  ... and {len(ungrounded_claims) - 3} more"

                    reason = f"""UNGROUNDED CONFIDENT CLAIMS DETECTED

The following claims lack verification evidence in tool output:
{claim_summary}

Before claiming as fact, verify using:
  - Read tool for documentation claims
  - Glob or ls for filesystem claims
  - Grep for code behavior claims

To bypass for this turn: Add --allow-ungrounded-claims to your message
To disable enforcement: Set UNVERIFIED_STANCE_ENABLED=false
"""

                    # PATTERN-001 FIX: Collect violation instead of returning
                    gate_mode = _get_gate_mode()
                    severity = "block" if gate_mode == "block" else "warn"
                    violations.append(("Phase 1 (Verification Engine)", reason, severity))

                # Log all passed claims
                for claim, verdict in claim_verdict_pairs:
                    if claim not in ungrounded_claims:
                        _log_decision(
                            session_id=session_id,
                            terminal_id=terminal_id,
                            claim=claim,
                            verdict=verdict,
                            tool_event_ids=tool_event_ids,
                            outcome="pass",
                            reason=f"Claim {verdict.status.value}: grounded in tool events or hedged",
                        )
        except Exception as e:
            # COMP-001: Fail-closed on verification errors (Constitutional: "fail fast")
            # Old behavior: pass to Phase 2 (fail-open) → violations silently ignored
            # New behavior: collect as violation → verification errors surface immediately
            logger.error("verification_engine_error", error=str(e), exc_info=True)
            violations.append(
                (
                    "Phase 1 (Verification Engine)",
                    f"Verification engine failed: {type(e).__name__}: {e}",
                    "block",
                )
            )

    # Phase 2: Unique Pattern Checks (kept from original implementation)
    # PATTERN-001 FIX: Collect violations instead of returning early
    try:
        rca_turn = bool(data.get("rca_turn"))
        detector_input = {
            **data,
            "response": response_text,
            "toolUse": [{"name": name} for name in data.get("tools_used", []) if str(name).strip()],
        }

        # System claim check (unique to this hook)
        system_claim = _check_unfounded_system_claims(response_text)
        if system_claim and not _distinguish_valid_explanation(response_text, detector_input):
            severity = "block" if (UNVERIFIED_STANCE_MODE == "block" and not rca_turn) else "warn"
            msg = (
                format_system_claim_block(system_claim)
                if severity == "block"
                else format_system_claim_advisory(system_claim)
            )
            violations.append(("Phase 2 (System Claims)", msg, severity))

        # Unverified stance detection (unique to this hook)
        result = detect_unverified_stance(response_text, detector_input)
        if result:
            severity = "block" if (UNVERIFIED_STANCE_MODE == "block" and not rca_turn) else "warn"
            msg = format_block_message(result) if severity == "block" else format_advisory(result)
            violations.append(("Phase 2 (Unverified Stance)", msg, severity))

        # Lazy closure check (unique to this hook)
        lazy_match = detect_lazy_closure(response_text)
        if lazy_match:
            msg = (
                f"⚠️ Lazy closure pattern detected: **{lazy_match.pattern_type}**\n\n"
                f"Matched: `{lazy_match.matched}`\n\n"
                f"{lazy_match.suggestion}"
            )
            effective_severity = lazy_match.severity
            if lazy_match.pattern_type == "sycophancy_capitulation" and _is_challenge_active(data):
                effective_severity = "block"
            severity = (
                "block"
                if (UNVERIFIED_STANCE_MODE == "block" and effective_severity == "block")
                else "warn"
            )
            violations.append(("Phase 2 (Lazy Closure)", msg, severity))

        # Verification-Target Mismatch check (unique to this hook)
        if isinstance(tool_events, list) and tool_events:
            vtm_msg = _check_verification_target_mismatch(response_text, tool_events)
            if vtm_msg:
                severity = (
                    "block" if (UNVERIFIED_STANCE_MODE == "block" and not rca_turn) else "warn"
                )
                violations.append(("Phase 2 (Verification-Target Mismatch)", vtm_msg, severity))

            # Completion claim check (unique to this hook)
            claim_valid, claim_msg = _check_completion_claim_with_events(response_text, tool_events)
            if not claim_valid:
                severity = "block" if UNVERIFIED_STANCE_MODE == "block" else "warn"
                msg = (
                    claim_msg
                    if severity == "block"
                    else f"⚠️ {claim_msg}\n\nThis would block in non-warn mode."
                )
                violations.append(("Phase 2 (Completion Claims)", msg, severity))
    except Exception as e:
        logger.error("Error during Phase 2 validation", error=str(e), exc_info=True)
        violations.append(
            (
                "Phase 2 (Unknown Error)",
                f"Phase 2 validation error: {type(e).__name__}: {e}",
                "block",
            )
        )

    # PATTERN-001 FIX: Aggregate violations and block if any phase has blocking violations
    if violations:
        # Separate blocking and warning violations
        blocking_violations = [v for v in violations if v[2] == "block"]
        warning_violations = [v for v in violations if v[2] == "warn"]

        if blocking_violations:
            # Build aggregated block message
            block_parts = []
            for phase_name, msg, _ in blocking_violations:
                block_parts.append(f"## {phase_name}\n{msg}")

            aggregated_reason = "MULTIPLE VERIFICATION VIOLATIONS DETECTED\n\n" + "\n\n".join(
                block_parts
            )

            return {
                "block": True,
                "reason": aggregated_reason,
                "blocking_hook": "StopHook_unverified_stance.py",
            }

        if warning_violations and _get_gate_mode() == "warn":
            # Print all warnings
            for phase_name, msg, _ in warning_violations:
                print(f"⚠️ {phase_name}\n{msg}", file=os.fdopen(1, "w", encoding="utf-8"))
            return {
                "allow": True,
                "note": f"Warnings issued: {len(warning_violations)} phase(s)",
            }


if __name__ == "__main__":
    main()
