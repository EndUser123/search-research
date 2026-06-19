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

UNCERTAINTY EXPRESSION — SPECIFIC LIMITATION + NEXT STEP
========================================================
When the model states something is unverified or uncertain, it should follow
the "specific limitation + next step" pattern:

  GOOD: "I have not run tests in this environment; this is not yet confirmed."
        "Next step: run pytest tests/test_foo.py and confirm all pass."

  BAD:  "this is unverified, but..." / "I believe it's correct but haven't tested"

Bare disclaimers like "this is unverified, but..." are treated as lazy closure
patterns and blocked. The preferred pattern explicitly names:
  (1) what is missing / unconfirmed (specific limitation)
  (2) what verification step would confirm it (next step)

This is the inverse of the completion-claim pattern: both enforce evidence-based
communication, but completion-claim requires runtime tool evidence for "fixed/tested"
claims, while this hook requires precise uncertainty language for "unverified" claims.
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
import re
import sys
import time
from pathlib import Path
from typing import Any

import structlog

HOOKS_DIR = _hooks_dir  # from bootstrap

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

# Shared evidence-scope loader
try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

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


def _adjudicate_candidate(response_text: str, tool_events: Any, phrase: str) -> str:
    """Semantic precision filter for a regex-flagged anti-dodge candidate.

    The surface-form regex is high-recall but high-false-positive (it fires on
    reasoning-about / quoting the system, not just genuine dodges). When enabled,
    the M3+Mistral adjudicator decides whether the matched candidate is a real
    work-dodge ('block') or a false positive ('allow').

    Fail-safe policy — fail OPEN, not closed (root-cause fix 2026-06-03):
      * disabled         -> 'block'  (preserve the legacy gate when the feature is off)
      * judge 'allow'    -> 'allow'  (confirmed false positive)
      * judge 'block'    -> 'block'  (confirmed genuine dodge — enforcement preserved)
      * judge 'unknown'  -> 'allow'  (providers timed out / rate-limited / keys missing)
      * judge-side error -> 'allow'

    Why fail OPEN on 'unknown'/error: this path is a HIGH-false-positive candidate by
    construction (the regex over-fires on use/mention). Failing CLOSED during a transient
    judge outage re-introduces exactly the false positive the judge exists to remove —
    which is what produced the wrongful 'self_referential_evasion' block on 2026-06-03
    when both providers were rate-limited. Capitulation-under-challenge is NOT routed here
    (it stays POLICY/block), so the strongest anti-sycophancy enforcement is unaffected.
    Every decision is logged (anti_dodge_decisions.jsonl) so a silent-off outage is
    observable instead of invisible. Default OFF via ANTI_DODGE_JUDGE_ENABLED.
    """
    if os.environ.get("ANTI_DODGE_JUDGE_ENABLED", "false").lower() != "true":
        return "block"
    verdict = "unknown"
    t0 = time.monotonic()
    try:
        from anti_dodge_judge import adjudicate as _adj

        events = tool_events if isinstance(tool_events, list) else []
        verdict = _adj(response_text, events, phrase)
    except Exception as e:  # judge-side failure (import/runtime) — fail open, logged
        verdict = f"error:{type(e).__name__}"
    # Fail-OPEN: only an explicit 'block' blocks; 'allow'/'unknown'/error all pass.
    decision = "block" if verdict == "block" else "allow"
    _log_adjudication(phrase, verdict, decision, (time.monotonic() - t0) * 1000.0, len(response_text or ""))
    return decision


# Logging configuration for verification engine decisions
LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_FILE = LOG_DIR / "unverified_stance.jsonl"
# Anti-dodge adjudication decision log — makes a silent judge-outage fail-open
# observable (verdict='unknown'/'error' with decision='allow' = enforcement was bypassed).
ADJUDICATION_LOG_FILE = LOG_DIR / "anti_dodge_decisions.jsonl"


def _log_adjudication(phrase: str, verdict: str, decision: str, latency_ms: float, text_len: int) -> None:
    """Append one adjudication decision to anti_dodge_decisions.jsonl (best-effort, never raises)."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": time.time(),
            "phrase": (phrase or "")[:120],
            "verdict": verdict,  # 'allow' | 'block' | 'unknown' | 'error:<Type>'
            "decision": decision,  # 'allow' | 'block' (what the gate actually did)
            "fail_open": verdict not in ("allow", "block"),  # True => judge was unavailable
            "latency_ms": round(latency_ms, 1),
            "text_len": text_len,
        }
        with ADJUDICATION_LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_tool_events_for_context(
    *, session_id: str, terminal_id: str, limit: int = 500
) -> list[dict[str, Any]] | None:
    """Compatibility wrapper for terminal-scoped/session-fresh evidence."""
    if load_scoped_tool_events is None:
        return None
    return load_scoped_tool_events(
        session_id=session_id,
        terminal_id=terminal_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


def load_tool_events(session_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Module-level loader used by completion/E2E checks and patchable in tests."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    return load_scoped_tool_events(
        session_id=session_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


# Discourse/hypothetical exemption — falsification conditionals and meta-commentary
# about the dialogue/contract are not verifiable factual claims and must not be gated
# as "ungrounded confident claims". Mirrors the ANALYSIS/MECHANISM type exemptions.
_DISCOURSE_EXEMPT = re.compile(
    r"\b(?:would|could|might)\s+be\s+(?:wrong|incorrect|a\s+mistake|false|invalid)\s+if\b"
    r"|\bwhat\s+would\s+(?:invalidate|falsify|change|disprove)\b"
    r"|\bby\s+design\b"
    r"|\bhypothetical(?:ly)?\b"
    r"|\bthe\s+(?:contract|rubric|protocol|instruction|guideline|spec)s?\s+(?:asks?|require|say|want)"
    r"|\bfor\s+the\s+record\b",
    re.IGNORECASE,
)


def _is_discourse_or_hypothetical(claim_text: str) -> bool:
    """Return True if the claim text is a falsification conditional or meta-discourse.

    These are statements ABOUT the dialogue/process or hypotheticals (e.g.
    "this would be wrong if ...", "the contract asks me to name ...") rather than
    empirical claims about code, the filesystem, or system behavior. They have no
    tool evidence to ground because there is nothing factual to verify.
    """
    return bool(claim_text and _DISCOURSE_EXEMPT.search(claim_text))


def _should_block_claim(
    claim: Claim,
    verdict: Any,
    loaded_events: list[dict] | None = None,
) -> bool:
    """Determine if a claim should be blocked based on verification verdict.

    Args:
        claim: The Claim object to evaluate
        verdict: VerificationVerdict from build_verdicts
        loaded_events: Tool events from this turn (used for content-match fallback on SILENT)

    Returns:
        True if claim should be blocked (ungrounded confident claim)
    """
    # ANALYSIS claims (value judgments, architectural opinions) don't require verification
    # These are subjective assessments like "X is valuable for Y" or "right idea, wrong contract"
    if claim.type == "ANALYSIS":
        return False

    # MECHANISM claims (internal code behavior without reading code) are epistemic
    # assessments about implementation internals — not verifiable factual claims
    if claim.type == "MECHANISM":
        return False

    # Hedged claims pass without evidence
    if claim.has_hedge:
        return False

    # Low confidence claims pass
    if claim.confidence < 0.7:
        return False

    # Discourse/hypothetical exemption — falsification conditionals and meta-commentary
    if _is_discourse_or_hypothetical(claim.text):
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

    # SILENT: check if claim content appeared in this turn's tool output
    if verdict.status == VerificationStatus.SILENT and loaded_events:
        from .verification.engine import _claim_matches_tool_output

        if _claim_matches_tool_output(claim, loaded_events):
            return False  # Content confirmed in tool output → don't block

    # SILENT status + confident claim = ungrounded
    return True


def _is_control_turn(response_text: str) -> bool:
    """Detect control/directive turns that should bypass verification.

    Control turns are short acknowledgments or directives that don't contain
    verifiable claims: "stop", "no", "yes", "ok", "done", "continue".
    """
    stripped = response_text.strip().lower()
    if len(stripped) < 1:
        return True  # Empty response
    if len(stripped) > 30:
        return False  # Long enough to contain real claims

    control_words = {
        "stop", "no", "yes", "ok", "okay", "done", "continue",
        "go ahead", "proceed", "skip", "cancel", "abort",
        "y", "n", "1", "0", "true", "false",
    }
    return stripped in control_words


def _should_block_enriched_claim(
    claim: Claim,
    enriched: Any,
    loaded_events: list[dict] | None = None,
) -> bool:
    """Determine if a claim should be blocked based on enriched verdict.

    Same semantics as _should_block_claim but also considers:
    - EnrichedVerdict.final_status (may be upgraded from SILENT)
    - CoverageReport.recommendation

    Args:
        claim: The Claim object to evaluate
        enriched: EnrichedVerdict from analyze_silent_verdicts
        loaded_events: Tool events from this turn
    """
    # ANALYSIS/MECHANISM/hedge/low-confidence exemptions (same as _should_block_claim)
    if claim.type in ("ANALYSIS", "MECHANISM"):
        return False
    if claim.has_hedge:
        return False
    if claim.confidence < 0.7:
        return False

    # Discourse/hypothetical exemption — falsification conditionals and meta-commentary
    if _is_discourse_or_hypothetical(claim.text):
        return False

    verdict = enriched.verdict

    # SUPPORTED, REFUTED, SELF_VERIFIED → don't block
    if verdict.status in (
        VerificationStatus.SUPPORTED,
        VerificationStatus.REFUTED,
        VerificationStatus.SELF_VERIFIED,
    ):
        return False

    # Check final_status from enrichment (may be upgraded from SILENT)
    final_status = getattr(enriched, "final_status", None)
    if final_status in (
        VerificationStatus.SUPPORTED,
        VerificationStatus.SELF_VERIFIED,
    ):
        return False  # Upgraded by decomposition/coverage/fallback

    # SILENT: check if claim content appeared in tool output (existing fallback)
    if verdict.status == VerificationStatus.SILENT and loaded_events:
        from .verification.engine import _claim_matches_tool_output

        if _claim_matches_tool_output(claim, loaded_events):
            return False

    # Check coverage recommendation
    coverage = getattr(enriched, "coverage", None)
    if coverage is not None:
        recommendation = getattr(coverage, "recommendation", "")
        if recommendation == "sufficient":
            return False  # Coverage analysis says evidence is sufficient

    # SILENT status + confident claim + no upgrade = ungrounded
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


# Relay attribution patterns — user attestation is authoritative per verification stack.
# When agent relays user-provided facts ("per your message, X is fixed"), no tool
# evidence should be required because the user is the authoritative source.
_RELAY_ATTRIBUTION_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bper\s+your\s+(?:message|report|note|update|description|prior\s+message)\b", re.I),
    re.compile(r"\byou(?:'ve|r?\s+have)\s+(?:indicated|said|noted|reported|mentioned|confirmed|told\s+me)\b", re.I),
    re.compile(r"\bas\s+you(?:'ve)?\s+(?:noted|said|indicated|reported|mentioned|confirmed)\b", re.I),
    re.compile(r"\baccording\s+to\s+you(?:r\s+(?:message|report|description))?\b", re.I),
    re.compile(r"\byou\s+(?:said|noted|reported|mentioned|confirmed|told\s+me)\s+(?:that\s+)?", re.I),
    re.compile(r"\byou'?ve\s+(?:indicated|confirmed|noted|reported|said|mentioned)\b", re.I),
    re.compile(r"\byou\s+(?:report|indicat|confirm)(?:ed|)(?:\s+that)?\b", re.I),
]

_RELAY_SENTENCE_SPLITTER = re.compile(r"(?<=[.!?\n])\s+")


def _is_relay_attributed(claim_text: str, full_response: str) -> bool:
    """Return True if claim_text appears in a relay-attributed sentence.

    Per CLAUDE.md verification stack: user-provided statements are authoritative
    evidence. When the agent relays what the user said, no tool evidence is required.
    """
    if not claim_text:
        return False
    key = claim_text[:60].lower().strip()
    if not key:
        return False
    sentences = _RELAY_SENTENCE_SPLITTER.split(full_response)
    for sentence in sentences:
        if key in sentence.lower():
            for pat in _RELAY_ATTRIBUTION_PATTERNS:
                if pat.search(sentence):
                    return True
    return False


def _strip_quoted_blocks(text: str) -> str:
    """Strip quoted/artifact blocks before pattern matching to prevent
    meta-discussion from self-retriggering the unfounded-claims detector.

    Strips:
    - Blockquote lines (starting with '>')
    - Inline quoted strings wrapping trigger phrases
    - Backtick/markdown code blocks
    - Stop hook feedback artifacts ('Stop (hook|says):', '⎿', etc.)
    - Epistemic format repair markers
    - Pattern-match diagnostic artifacts
    """
    import re as _re

    result = []

    # Strip triple-backtick code blocks first (multiline)
    # Use a non-greedy match to avoid stripping entire response
    code_block_pattern = _re.compile(r"```[\s\S]*?```", _re.MULTILINE)
    text = code_block_pattern.sub("", text)

    # Strip single-backtick inline code spans
    inline_code_pattern = _re.compile(r"`[^`\n]+`")
    text = inline_code_pattern.sub("", text)

    # Strip inline double-quoted strings that wrap trigger phrase patterns
    # Phase 1: strip whole-string matches (trigger IS the entire quoted content)
    quoted_trigger_pattern = _re.compile(
        r"""["']Since\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+["']|"""
        r"""["']Because\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+["']|"""
        r"""["']As\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+["']|"""
        r"""["']The\s+system\s+(?:does\s+not|doesn't|can't|cannot)\s+\w+["']|"""
        r"""["']There's\s+no\s+hook\s+for["']|"""
        r"""["']No\s+hook\s+exists\s+that["']|"""
        r"""["']We\s+can't\s+\w+\s+because\s+the\s+\w+["']|"""
        r"""["']Unable\s+to\s+\w+\s+due\s+to\s+(?:the\s+)?\w+["']""",
        _re.IGNORECASE,
    )
    text = quoted_trigger_pattern.sub("", text)

    # Phase 2: strip trigger phrase content FROM WITHIN longer quoted strings
    # Catches: "Root cause: since the hook blocks this path"
    # where the trigger is embedded within a longer quoted string
    embedded_trigger_pattern = _re.compile(
        r'''(["'])(.*?)\1''',
        _re.DOTALL,
    )

    def _strip_trigger_within_quotes(m: re.Match) -> str:
        """Remove trigger phrase content from within a quoted string."""
        quote_char = m.group(1)
        content = m.group(2)
        # Strip trigger phrases from within the quoted content
        inner_stripped = _re.sub(
            r"""Since\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+|"""
            r"""Because\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+|"""
            r"""As\s+(?:the\s+)?(?:\w+\s+)?hook\s+\w+|"""
            r"""The\s+system\s+(?:does\s+not|doesn't|can't|cannot)\s+\w+|"""
            r"""There's\s+no\s+hook\s+for|"""
            r"""No\s+hook\s+exists\s+that|"""
            r"""We\s+can't\s+\w+\s+because\s+the\s+\w+|"""
            r"""Unable\s+to\s+\w+\s+due\s+to\s+(?:the\s+)?\w+""",
            "",
            content,
            flags=_re.IGNORECASE,
        )
        # Collapse extra whitespace
        inner_stripped = _re.sub(r"\s+", " ", inner_stripped).strip()
        if inner_stripped:
            return quote_char + inner_stripped + quote_char
        return ""

    text = embedded_trigger_pattern.sub(_strip_trigger_within_quotes, text)

    # Drop blockquote lines entirely (don't keep their content)
    for line in text.splitlines():
        stripped = line.lstrip("> \t")
        # Detect blockquotes: starts with '>' OR contains a '> ' cell in a markdown table row
        is_blockquote = line.startswith(">") or (
            "|" in line and any(
                cell.startswith("> ") for cell in (c.strip() for c in line.split("|"))
            )
        )
        if stripped and not is_blockquote:
            result.append(line)
        elif is_blockquote:
            pass  # Drop entire blockquote line
        else:
            result.append(line)

    text = "\n".join(result)

    # Strip Stop hook artifacts
    result = []
    for line in text.splitlines():
        # Skip stop hook feedback artifacts
        lower = line.lower()
        if any(
            lower.startswith(prefix)
            for prefix in (
                "stop hook says:",
                "stop hook:",
                "stop:",
                "⎿",  # Hook feedback indent
                "lazy workaround",
                "epistemic format repair",
                "pattern matched:",
                "required approach:",
                "remember:",
                "this suggests",
                "this is a",
            )
        ):
            continue
        result.append(line)

    return "\n".join(result)


def _check_unfounded_system_claims(response: str, data: dict | None = None) -> str | None:
    """Check for unfounded system claims (hook/system capability statements without evidence).

    Args:
        response: The assistant's response text.
        data: Optional dict with 'toolUse' key for evidence checking. If None, skips
              evidence discrimination (backward-compatible for callers that don't pass data).

    Returns:
        Matched phrase if unfounded claim detected without valid evidence, else None.
    """
    # Strip quoted/artifact blocks before pattern matching to prevent meta-discussion
    # from self-retriggering (SHOULD-001 extension: quoted blocks, hook feedback, code)
    stripped = _strip_quoted_blocks(response)

    for pattern in UNFOUNDED_SYSTEM_CLAIM_PATTERNS:
        match = pattern.search(stripped)
        if match:
            # Discriminate: valid explanation = verification tools used OR evidence phrases present
            if data is not None and _distinguish_valid_explanation(response, data):
                return None  # Valid evidence — allow
            return match.group(0)
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
        # User attribution is authoritative evidence per verification stack
        *_RELAY_ATTRIBUTION_PATTERNS,
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
    re.compile(r"/\S+\s+skill\s+(?:executed|completed|ran)\b", re.IGNORECASE),
    re.compile(r"/\S+\s+skill\s+(?:is\s+)?(?:fully\s+)?(?:functional|working)\b", re.IGNORECASE),
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
# FIX-005: _DOC_ONLY_TOOL_NAMES deleted.
# Replaced by RUNTIME_TOOLS check in _check_verification_target_mismatch above.
# Read is now accepted as valid runtime evidence (as it should be).

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
        from anti_sycophancy.challenge_marker import challenge_marker_path as _cmp

        marker = _cmp(session_id, terminal_id)
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


_CALLOUT_PHRASES = frozenset({
    "sycophant", "sycophancy", "capitulat", "flip your", "position flip",
    "agree with me", "you just agreed", "you changed your", "stop agreeing",
    "did you just agree",
})


def _is_callout_message(user_message: str) -> bool:
    """Return True if user explicitly named sycophantic behavior.

    When the user calls out sycophancy directly, the AI's admission response
    ("Yes, I was being sycophantic") must not be blocked — deadlock otherwise.
    """
    lower = user_message.lower()
    return any(phrase in lower for phrase in _CALLOUT_PHRASES)


def _consume_challenge_marker(data: dict[str, Any]) -> None:
    """Delete challenge marker to enforce single-use semantics (Recommendation 3).

    The marker is written per-turn by anti_sycophancy_injector.py. Deleting it here
    prevents a follow-up message from being incorrectly gated after the challenge
    response has already been evaluated.
    """
    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    )
    session_id = str(
        data.get("session_id") or data.get("sessionId") or os.environ.get("CLAUDE_SESSION_ID", "")
    )

    def _safe(v: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", v) if v else "unknown"

    try:
        from anti_sycophancy.challenge_marker import challenge_marker_path as _cmp

        marker = _cmp(session_id, terminal_id)
    except Exception:
        marker = (
            HOOKS_DIR
            / "state"
            / "anti_sycophancy_injector"
            / f"challenge__{_safe(session_id)}__{_safe(terminal_id)}.json"
        )

    try:
        if marker.exists():
            marker.unlink()
    except OSError:
        pass


def _check_verification_target_mismatch(
    response: str, tool_events: list[dict[str, Any]]
) -> str | None:
    """Flag runtime behavior claims without runtime evidence.

    Fires when:
    - Response claims something "works" / "runs" / is "working as intended"
    - NO runtime tools (Bash/Edit/Read/Grep/Glob) were used

    RUNTIME_TOOLS are valid evidence types. If Read was used to verify code,
    that's legitimate evidence — the old _DOC_ONLY_TOOL_NAMES=Solid{Skill} logic
    was wrong (FIX-005) because it excluded Read from accepted evidence.
    """
    if not _RUNTIME_CLAIM_PATTERN.search(response):
        return None
    if not tool_events:
        return None
    tool_names = {e.get("name", "") for e in tool_events if isinstance(e, dict)}
    non_empty_tools = tool_names - {""}
    # If any runtime tool was used, claim has valid evidence — allow
    if non_empty_tools & RUNTIME_TOOLS:
        return None
    # No runtime tools used but claim about runtime behavior — flag it
    if non_empty_tools:
        return (
            "⚠️ **Verification-Target Mismatch**: Runtime behavior claim without runtime evidence.\n\n"
            "You claimed something 'works' or 'runs' but used no Bash, Read, Grep, Glob, or Edit tools.\n"
            "Provide actual evidence: tool output, file content, command results.\n"
            f"Tools used: {sorted(non_empty_tools)}"
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
        # Check cache first (PERF-001)
        if session_id in _EVIDENCE_CACHE:
            tool_events = _EVIDENCE_CACHE[session_id]
        else:
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

        # Control-turn bypass: skip verification for short directive turns
        if _is_control_turn(response_text):
            return {"allow": True, "reason": "Control turn — verification skipped"}
        try:
            # Extract claims using verification engine
            claims = extract_claims(response_text)

            # Exempt relay-attributed claims — user attestation is authoritative
            # per the CLAUDE.md verification stack ("User Context: Always").
            claims = [c for c in claims if not _is_relay_attributed(c.text, response_text)]

            if claims:
                # Load tool events for context (terminal-scoped)
                # If tool_events provided in data, merge with session-scoped events
                # FIX: Avoid self-extend bug (LOGIC-001) - was extending loaded_events with itself
                # FIX: Add deduplication by event ID to prevent TOCTOU duplicates
                if isinstance(tool_events, list) and tool_events:
                    session_events = load_tool_events_for_context(
                        session_id=session_id,
                        terminal_id=terminal_id,
                        limit=500,
                    ) or []
                    # Merge session + turn events, deduplicate by event ID
                    combined = session_events + tool_events
                    seen: set[str] = set()
                    loaded_events = [
                        e for e in combined
                        if (eid := e.get("id", "")) not in seen and not seen.add(eid)
                    ]
                else:
                    loaded_events = load_tool_events_for_context(
                        session_id=session_id,
                        terminal_id=terminal_id,
                        limit=500,
                    ) or []

                # Extract tool event IDs for logging
                tool_event_ids = [event.get("id", 0) for event in loaded_events]

                # Build verification verdicts using engine
                verdicts = build_verdicts(claims, loaded_events)

                # Second-stage analysis: decomposition + coverage for SILENT verdicts
                try:
                    from verification.engine import analyze_silent_verdicts as _analyze_silent
                    enriched_verdicts = _analyze_silent(verdicts, claims, loaded_events)
                except Exception:
                    # Fail-open: wrap original verdicts as unenriched
                    from verification.engine import EnrichedVerdict as _EV
                    enriched_verdicts = [
                        _EV(
                            verdict=v, decomposition=None, sub_verdicts=(),
                            coverage=None, recommendation=None,
                            final_status=v.status, final_confidence=v.confidence,
                        )
                        for v in verdicts
                    ]

                # Evaluate each claim against its enriched verdict
                ungrounded_claims = []
                claim_verdict_pairs = []

                for claim, enriched in zip(claims, enriched_verdicts):
                    claim_verdict_pairs.append((claim, enriched.verdict))
                    if _should_block_enriched_claim(claim, enriched, loaded_events):
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
        except ImportError as e:
            # ImportError is a structural bug in the verification engine's dependencies,
            # not a response violation the LLM can fix. Log it but don't block.
            logger.error("verification_engine_import_error", error=str(e), exc_info=True)
            violations.append(
                (
                    "Phase 1 (Verification Engine)",
                    f"Verification engine import failed (non-blocking): {type(e).__name__}: {e}",
                    "warn",
                )
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

    # Consume challenge marker once per response (single-use - Recommendation 3).
    # Callout exemption: if the user explicitly named sycophancy, exempt the admission
    # response from the capitulation and protocol-adherence gates to avoid deadlock.
    _user_message = str(data.get("user_message", "") or data.get("prompt", "") or "")
    challenge_active = _is_challenge_active(data)
    if challenge_active:
        _consume_challenge_marker(data)
        if _is_callout_message(_user_message):
            challenge_active = False

    # Phase 2: Unique Pattern Checks (kept from original implementation)
    # PATTERN-001 FIX: Collect violations instead of returning early
    try:
        rca_turn = bool(data.get("rca_turn"))
        detector_input = {
            **data,
            "response": response_text,
            "toolUse": [{"name": name} for name in data.get("tools_used", []) if str(name).strip()],
        }

        # System claim check (unique to this hook) — with evidence discrimination
        system_claim = _check_unfounded_system_claims(response_text, detector_input)
        if system_claim and not _distinguish_valid_explanation(response_text, detector_input):
            if _adjudicate_candidate(response_text, tool_events, system_claim) == "allow":
                pass  # M3 judge confirmed false positive (reasoning / quote / evidence-backed)
            else:
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
        # FIX 1c: Compute bash_ran from tool_events and pass to detector
        bash_ran = False
        if isinstance(tool_events, list):
            for event in tool_events:
                # Presence of a Bash event this turn = bash ran (event only exists if invoked).
                if isinstance(event, dict) and event.get("name") == "Bash":
                    bash_ran = True
                    break
        lazy_match = detect_lazy_closure(response_text, has_bash_evidence=bash_ran)
        if lazy_match:
            _is_capitulation = lazy_match.pattern_type == "sycophancy_capitulation"
            # Precision filter for NON-capitulation patterns (declaration etc.), which have a
            # high false-positive rate on use/mention. Capitulation-under-challenge stays
            # POLICY and is never adjudicated away.
            if (not _is_capitulation) and _adjudicate_candidate(
                response_text, tool_events, lazy_match.matched
            ) == "allow":
                pass  # M3 judge confirmed false positive (quote / mention / fulfilled work)
            else:
                msg = (
                    f"⚠️ Lazy closure pattern detected: **{lazy_match.pattern_type}**\n\n"
                    f"Matched: `{lazy_match.matched}`\n\n"
                    f"{lazy_match.suggestion}"
                )
                effective_severity = lazy_match.severity
                if _is_capitulation and challenge_active:
                    effective_severity = "block"
                # Fix 2: sycophancy_capitulation blocks when challenge is active regardless of mode.
                # Other pattern types still respect UNVERIFIED_STANCE_MODE.
                severity = (
                    "block"
                    if effective_severity == "block"
                    else ("block" if UNVERIFIED_STANCE_MODE == "block" else "warn")
                )
                violations.append(("Phase 2 (Lazy Closure)", msg, severity))

        # Fix 3: Enforce ADVOCATE_PROTOCOL adherence when a challenge is active.
        # The injector requires STATUS: labels on every claim after a challenge. This gate
        # blocks responses that have neither STATUS: labels nor tool verification evidence.
        # Known limitation: STATUS: labels can be inserted without genuine evidence
        # (adversarial adaptation). This check catches accidents, not deliberate intent.
        if challenge_active and len(response_text) > 350:
            has_status_labels = "STATUS:" in response_text.upper()
            has_verification_evidence = any(
                e.get("name") in ("Bash", "Read", "Grep", "Glob", "WebSearch", "WebFetch")
                for e in (tool_events if isinstance(tool_events, list) else [])
            )
            if not has_status_labels and not has_verification_evidence:
                protocol_msg = (
                    "❌ **Protocol Adherence Required During Active Challenge**\n\n"
                    "A challenge is active but your response contains no STATUS: labels "
                    "or tool verification evidence.\n\n"
                    "Per ADVOCATE_PROTOCOL, each factual claim requires:\n"
                    "  STATUS: TESTED_IN_ENV — ran with Bash and saw output\n"
                    "  STATUS: INFERRING_FROM_CODE — read source, reasoning about behavior\n"
                    "  STATUS: INFERRING_FROM_DOCS — documentation only\n\n"
                    "⚠️ Note: STATUS: labels catch accidental omissions but do not prevent "
                    "adversarial insertion of labels without evidence. This is a known limitation.\n\n"
                    "Add STATUS: labels to your claims or provide tool verification evidence."
                )
                violations.append(("Phase 2 (Protocol Adherence)", protocol_msg, "block"))

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
