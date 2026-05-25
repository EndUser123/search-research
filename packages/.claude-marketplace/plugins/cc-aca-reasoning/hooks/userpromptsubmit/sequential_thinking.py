"""Sequential thinking trigger detection hook.

Detects complex/analytical intent in user prompts and creates state files for
sequential thinking sessions. Provides multi-terminal safety via terminal_id field.

Trigger patterns (intent-based - match naturally typed requests):
- Analysis & evaluation: analyze, evaluate, assess, examine, investigate, review, explain, understand
- Problem-solving: debug, diagnose, troubleshoot, identify issue/bug/cause
- Design decisions: should I/we..., compare/contrast, which approach/option
- Architecture: design/architect/refactor system/service/module/api/schema
- Complex explanation: why does/is/isn't/doesn't..., how does/come/would... (longer questions)

Guards:
- Hard floor (15 chars): Never trigger, even if pattern matches
- Soft floor (15-40 chars): Require 2+ signals (pattern match + technical depth)
- Normal (>=40 chars): Single pattern match sufficient
- Negative patterns: Explicitly block config values and trivial questions

Semantic Detection (RAM Optimization):
- Uses unified_semantic_daemon for shared sentence-transformer model across terminals
- RAM: ~90MB per terminal -> ~100MB shared total
- Fallback chain: daemon IPC -> direct SentenceTransformer -> regex-only
- Threshold: >0.70 strong match (trigger), 0.50-0.70 partial (secondary signal)
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import re
import sys
import uuid
from pathlib import Path
from typing import Optional

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.reasoning_contract import (
    append_reasoning_contract,
    mark_reasoning_contract_applied,
    reasoning_contract_already_applied,
)
from UserPromptSubmit_modules.registry import register_hook
from UserPromptSubmit_modules.unified_detection import (
    UnifiedDetectionResult,
    ensure_unified_detection_result,
)

# Ensure __lib is importable (hooks dir is already in sys.path via UserPromptSubmit.py)
def _find_hooks_dir() -> Path:
    """Locate the hooks root that contains __lib/sequential_state.py."""
    source_path = Path(__file__).resolve()
    for candidate in source_path.parents:
        if (candidate / "__lib" / "sequential_state.py").exists():
            return candidate
    return source_path.parent.parent


_HOOKS_DIR = _find_hooks_dir()
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))
from UserPromptSubmit_modules.sequential_thinking_semantic_client import (  # noqa: E402
    compute_similarity,
)

# ---------------------------------------------------------------------------
# Semantic Trigger Detection (Embedding-Based via Daemon)
# ---------------------------------------------------------------------------
# Uses the unified_semantic_daemon to share the sentence-transformer model
# across all terminals, reducing per-terminal RAM from ~90MB to ~100MB shared.
#
# Fallback chain:
# 1. Try daemon IPC (compute_embedding action + local cosine similarity)
# 2. Fall back to direct SentenceTransformer loading if daemon unavailable
# 3. Fall back to regex-only if semantic computation fails completely
#
# Threshold guidance:
#   - Score > 0.70: Strong match (trigger)
#   - Score 0.50-0.70: Partial match (use as secondary signal)
#   - Score < 0.50: Weak/no match

_SEMANTIC_SIMILARITY_THRESHOLD = 0.70  # Trigger on strong match
_SEMANTIC_PARTIAL_THRESHOLD = 0.50  # Use as secondary signal


def _should_trigger_semantic(prompt: str) -> tuple[bool | None, Optional[str]]:
    """Determine if prompt should trigger sequential thinking via semantic similarity.

    Uses two-tier threshold:
    - Strong match (>=0.70): Direct trigger (returns True)
    - Partial match (>=0.50): Secondary signal (returns None - use with regex)
    - Weak match (<0.50): No trigger (returns False)

    Returns:
        Tuple of (should_trigger, matched_phrase)
        - True + phrase: Strong match, trigger directly
        - None + phrase: Partial match, use as secondary signal with regex
        - False + None: No match
    """
    if len(prompt.strip()) <= _HARD_FLOOR:
        return False, None

    score, matched_phrase = compute_similarity(prompt)

    if score >= _SEMANTIC_SIMILARITY_THRESHOLD:
        return True, matched_phrase

    if score >= _SEMANTIC_PARTIAL_THRESHOLD:
        # Partial match - use as secondary signal if regex also matches
        return None, matched_phrase  # Signal that semantic similarity is available

    return False, None


# Thresholds for multi-signal gating
_HARD_FLOOR = 15  # Never trigger below this
_SOFT_FLOOR = 30  # Require 2+ signals below this (lowered from 40 for question patterns)

# Invariant assertion: hard floor must be less than soft floor
assert _HARD_FLOOR < _SOFT_FLOOR, (
    f"HARD_FLOOR ({_HARD_FLOOR}) must be less than SOFT_FLOOR ({_SOFT_FLOOR})"
)

# Negative patterns that prevent triggering even if positive pattern matches
_NEGATIVE_PATTERNS = [
    r"debug\s*(?:mode|flag|level)\s*[:=]",  # "debug mode: true", "debug flag = 1"
    r"debug\s*(?:enabled|disabled|on|off)",  # "debug enabled", "debug off"
    r"how\s+(?:does|do)\s+(?:this|it)\s+look\b",  # "how does this look?" (trivial)
    r"what\s+does\s+(?:this|that|it)\s+do\b",  # "what does this do?" (often casual)
    r"^.{1,20}\?$",  # Very short questions ending with ?
]

# Technical depth indicators that signal genuine analytical intent
_TECHNICAL_INDICATORS = [
    "because", "issue", "problem", "error", "fails", "bug", "unexpected", "broken",
    "crash", "exception", "traceback", "incorrect", "wrong", "difference", "compare",
    "versus", "vs", "tradeoff", "alternative", "better", "optimize", "improve",
    "refactor", "architecture", "design", "pattern", "code", "function", "module",
    "service", "api", "root", "cause", "risk", "security", "performance", "detail",
    "option", "approach", "method", "strategy", "way", "efficient", "coupling",
    "scale", "scalable", "best", "works", "handles", "reduces", "edge case", "mechanism",
    "load", "connection", "timing", "out", "timeout", "distributed", "database",
    "migration", "deadlock", "consistency", "flow", "leak", "memory", "intermittent",
    "limit", "rate", "safely", "profile", "concern", "inject", "dependency",
]

SEQUENTIAL_THINKING_PATTERNS = [
    # Analysis & evaluation (added: review, explain, understand, clarify)
    r"\b(?:analyze|analyse|evaluate|assess|examine|investigate|review|explain|understand|clarify)\b",
    # Problem-solving
    r"\b(?:debug|diagnose|troubleshoot)\b",
    r"\bidentif(?:y|ying)\s.{0,30}(?:issue|problem|bug|cause|root)\b",
    # Design decisions with tradeoffs (fixed: handle contractions)
    r"\bshould(?:n't|'ve| not)\s+(?:i|we)\s.{15,}",
    r"\b(?:compare|contrast)\b.{0,40}\b(?:between|vs|versus)\b",
    r"\b(?:which|what(?:'s)?)\s.{0,30}(?:approach|option|strategy|way|method)\b",
    # Architecture/refactoring with scope
    r"\b(?:design|architect|refactor|restructure)\b.{0,40}\b(?:system|service|module|api|schema)\b",
    # Complex explanation of mechanisms (added: negations, "how come", contractions)
    r"\b(?:why\s+(?:does|is|do|are|doesn't|isn't|don't|aren't|won't|can't)|how\s+(?:does|do|would|should|come))\b.{10,}",
    # Interrogative patterns
    r"\bwhat\s+(?:is|are|does|do|can|should|would|could|will)\b",
    r"\bhow\s+(?:does|do|can|should|would|could|to|come)\b",
    r"\bwhy\s+(?:does|is|do|are|was|were|has|have|should)\b",
    r"\bwhen\s+(?:does|is|do|are|was|were|should|will|would)\b",
    r"\bwhere\s+(?:is|are|does|do|was|were|can|should)\b",
    r"\b(?:can|could|would|should)\s+(?:i|you|we)\b",
    r"\b(?:is|are|does|do|was|were|has|have)\s+(?:there|this|that|it|he|she|they)\b",
    # Whether questions (meta-analytical: whether X should/does/could)
    r"\bwhether\s+(?:this|that|it|we|I|they)\s+(?:should|would|could|might)\b",
]

# Hypothesis mode trigger patterns
HYPOTHESIS_MODE_PATTERNS = [
    r"\bmaintain\s+multiple\s+hypotheses\b",
    r"\bcompeting\s+hypotheses\b",
    r"\bparallel\s+explanations\b",
    r"\bwhat\s+(?:are|could\s+be)\s+(?:the\s+)?(?:possible|alternative)\s+explanations\b",
]

# Investigation intent pattern for Layer 2 "Investigation Mode"
_INVESTIGATION_RE = re.compile(
    r"\b(debug|investigate|diagnose|analyze|explain\s+why|root\s+cause|"
    r"figure\s+out|what's\s+wrong|what\s+caused|troubleshoot|"
    r"why\s+does|why\s+is|why\s+did|how\s+does|what\s+happens|"
    r"characterize|classify|problem\s+domain|investigation)\b",
    re.IGNORECASE,
)

# CHANGE-005: RCA/Self-investigation trigger — matches skill invocation patterns
_SELF_INVESTIGATION_RE = re.compile(
    r"\b(/rca|/rca\s|root\s+cause\s+analysis|root\s+cause\s+diagnostic|"
    r"why\s+is\s+.*\s+lazy|why\s+is\s+.*\s+broken|why\s+does\s+.*\s+fail|"
    r"diagnose\s+this|debug\s+this|rca\s+skill)\b",
    re.IGNORECASE,
)

# Proactive Investigation Mode Instructions (Layer 2)
_INVESTIGATION_INSTRUCTIONS = (
    "Hypotheses → Testing → Conclusion:\n"
    "1) Generate 3+ competing hypotheses and note what would confirm or falsify each.\n"
    "2) Test the best candidates with tools.\n"
    "3) State root cause only after at least 2 hypotheses are tested."
)


def _extract_trigger_phrase(prompt: str, pattern: str) -> str:
    match = re.search(pattern, prompt, re.IGNORECASE)
    return match.group(0) if match else pattern


def _matches_negative_pattern(prompt: str) -> bool:
    """Check if prompt matches any negative pattern (should not trigger)."""
    prompt_lower = prompt.lower()
    for pattern in _NEGATIVE_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True
    return False


def _has_technical_depth(prompt: str) -> bool:
    """Check if prompt contains technical depth indicators."""
    prompt_lower = prompt.lower()
    return any(indicator in prompt_lower for indicator in _TECHNICAL_INDICATORS)


def _create_sequential_state(
    session_id: uuid.UUID,
    trigger_phrase: str,
    terminal_id: str,
    metadata: dict[str, object],
) -> None:
    """Persist sequential-thinking session state when the helper package is available."""
    try:
        from __lib.sequential_state import create_state

        create_state(session_id, trigger_phrase, terminal_id, metadata)
    except Exception:
        # Fail open: sequential thinking should still inject guidance even if state storage is unavailable.
        pass


def _shared_sequential_signal(
    unified_result: UnifiedDetectionResult | None,
) -> tuple[bool, bool, str | None]:
    """Translate unified detection into sequential-thinking trigger signals."""
    if unified_result is None:
        return False, False, None

    matched_modes = set(unified_result.matched_modes)
    matched_frameworks = set(unified_result.matched_frameworks)
    diagnostic_intents = {"diagnostic", "implementation_diagnostic"}
    investigation_frameworks = {
        "calibrated_confidence",
        "cynefin_classification",
        "hanlons_razor",
        "named_artifact_discovery",
    }

    is_investigation = bool(
        unified_result.intent_classification in diagnostic_intents
        or matched_frameworks & investigation_frameworks
    )
    should_trigger = bool(
        matched_modes & {"sequential", "multi_agent", "graph", "two_stage"}
        or is_investigation
    )
    if not should_trigger:
        return False, is_investigation, None

    phrase_parts: list[str] = []
    if unified_result.intent_classification:
        phrase_parts.append(f"intent={unified_result.intent_classification}")
    if unified_result.matched_modes:
        phrase_parts.append("modes=" + ", ".join(unified_result.matched_modes[:3]))
    if unified_result.matched_profiles:
        phrase_parts.append(
            "profiles=" + ", ".join(unified_result.matched_profiles[:3])
        )

    trigger_phrase = (
        "unified detection"
        if not phrase_parts
        else "unified detection: " + "; ".join(phrase_parts)
    )
    return True, is_investigation, trigger_phrase


def _sequential_addendum() -> str:
    """Return the minimal sequential-thinking addendum when the base contract is already active."""
    return (
        "SEQUENTIAL THINKING ADDENDUM:\n"
        "- Keep 2-3 competing explanations or steps in view until the evidence narrows them.\n"
        "- Name the smallest discriminating check before concluding.\n"
        "- Preserve rollback or fallback notes only if the prompt has real blast radius."
    )


@register_hook("sequential_thinking", priority=8.5)
def sequential_thinking_hook(context: HookContext) -> HookResult:
    """Detect sequential thinking triggers and inject session context."""
    # Skip skill invocations
    if context.prompt.strip().startswith("/"):
        return HookResult.empty()

    prompt = context.prompt
    prompt_lower = prompt.lower()
    terminal_id = context.terminal_id or ""
    unified_result = ensure_unified_detection_result(context)
    shared_triggered, shared_investigation, shared_phrase = _shared_sequential_signal(
        unified_result
    )

    # Detect investigation mode (Layer 2)
    is_investigation = bool(_INVESTIGATION_RE.search(prompt_lower) or shared_investigation)

    # CHANGE-005: Detect self-investigation mode (RCA skill invoked)
    is_self_investigation = bool(_SELF_INVESTIGATION_RE.search(prompt_lower))
    if is_self_investigation:
        is_investigation = False  # Self-investigation supersedes generic investigation

    # Detect hypothesis mode
    is_hypothesis_mode = False
    for pattern in HYPOTHESIS_MODE_PATTERNS:
        if re.search(pattern, prompt_lower):
            is_hypothesis_mode = True
            break

    # Hypothesis mode supersedes investigation — both should never be true.
    # ARCH-001: Modes serve different purposes; hypothesis mode prevents overfitting,
    # investigation mode provides structured RCA/debugging workflow.
    if is_hypothesis_mode:
        is_investigation = False

    # Check for positive pattern match first
    matched_pattern = None
    for pattern in SEQUENTIAL_THINKING_PATTERNS:
        if re.search(pattern, prompt_lower):
            matched_pattern = pattern
            break

    # Check semantic trigger (secondary signal)
    semantic_triggered = False
    semantic_phrase = None
    try:
        sem_result, sem_phrase = _should_trigger_semantic(prompt)
        semantic_triggered = sem_result is True
        semantic_phrase = sem_phrase
    except Exception:
        semantic_triggered = False
        semantic_phrase = None

    # If neither regex nor semantic triggered, don't trigger
    if (
        not matched_pattern
        and not semantic_triggered
        and not is_hypothesis_mode
        and not shared_triggered
    ):
        return HookResult.empty()

    # Apply gating logic
    prompt_len = len(prompt.strip())

    if _matches_negative_pattern(prompt):
        return HookResult.empty()

    if prompt_len <= _HARD_FLOOR:
        return HookResult.empty()

    # Injection formatting helper
    def _get_injection(session_id: uuid.UUID, trigger_phrase: str, is_investigation: bool, is_hypothesis_mode: bool, is_self_investigation: bool = False) -> HookResult:
        metadata = {"is_investigation": is_investigation}
        if is_hypothesis_mode:
            metadata["hypothesis_mode"] = True
            metadata["max_iterations"] = 2
        if is_self_investigation:
            metadata["is_self_investigation"] = True
            metadata["max_iterations"] = 2

        _create_sequential_state(session_id, trigger_phrase, terminal_id, metadata)

        if is_hypothesis_mode:
            mode_text = "multi_hypothesis"
            instructions = (
                "Maintain 2-3 competing explanations and evaluate each against evidence before concluding."
            )
        elif is_self_investigation:
            mode_text = "self_investigation"
            instructions = (
                "MANDATORY PRE-FLIGHT: Trace all files, git history, state artifacts, and MCP resources "
                "BEFORE asking the user to check anything. Trace it yourself."
            )
        elif is_investigation:
            mode_text = "investigation"
            instructions = _INVESTIGATION_INSTRUCTIONS
        else:
            mode_text = "initial"
            instructions = (
                "Work step-by-step, then check the answer against evidence before concluding."
            )

        injection = (
            f"Sequential thinking enabled.\n\n"
            f"<sequential_thinking>\n"
            f"Session ID: {session_id}\n"
            f"Trigger: {trigger_phrase}\n"
            f"Mode: {mode_text} (iteration 0 of 2)\n"
            f"</sequential_thinking>\n\n"
            f"{instructions}\n"
        )
        if reasoning_contract_already_applied(context):
            injection = f"{injection}\n{_sequential_addendum()}"
        else:
            injection = append_reasoning_contract(
                injection,
                include_verification=True,
                include_counterexample=True,
                include_discovery=False,
                include_rollback=True,
                include_evidence=True,
            )
            mark_reasoning_contract_applied(context, "sequential_thinking")
        return HookResult(
            context={
                "additionalContext": injection,
                "suppress": [
                    "operating_rules",
                ],
            },
            tokens=200,
        )

    # Hypothesis mode trigger (highest priority)
    if is_hypothesis_mode:
        return _get_injection(uuid.uuid4(), "hypothesis mode trigger", False, True)

    # CHANGE-005: Self-investigation mode trigger — fires on RCA/diagnostic skill invocation
    if is_self_investigation:
        return _get_injection(uuid.uuid4(), "self-investigation trigger", False, False, True)

    # Strong semantic match (>0.70)
    if semantic_triggered and not matched_pattern:
        return _get_injection(uuid.uuid4(), semantic_phrase or "semantic similarity match", is_investigation, False)

    if shared_triggered and not matched_pattern and not semantic_triggered:
        return _get_injection(
            uuid.uuid4(),
            shared_phrase or "unified detection",
            is_investigation,
            False,
        )

    # Above soft floor
    if prompt_len >= _SOFT_FLOOR:
        if matched_pattern or semantic_triggered or shared_triggered:
            trigger_phrase = (
                _extract_trigger_phrase(prompt, matched_pattern)
                if matched_pattern
                else (
                    semantic_phrase
                    or shared_phrase
                    or "semantic similarity match"
                )
            )
            return _get_injection(uuid.uuid4(), trigger_phrase, is_investigation, False)

    # Soft floor zone (15-30 chars)
    _INTERROGATIVE_KEYWORDS = ["should", "can", "could", "would", "what", "how", "why", "when", "where", "whether"]

    def _is_interrogative_match() -> bool:
        if not matched_pattern: return False
        pattern_lower = matched_pattern.lower()
        return any(kw in pattern_lower for kw in _INTERROGATIVE_KEYWORDS)

    signals = 0
    if matched_pattern: signals += 1
    if semantic_phrase and not _is_interrogative_match(): signals += 1
    if _has_technical_depth(prompt): signals += 1
    if shared_triggered: signals += 1

    if signals >= 2:
        trigger_phrase = (
            _extract_trigger_phrase(prompt, matched_pattern)
            if matched_pattern
            else (semantic_phrase or shared_phrase or "combined signals")
        )
        return _get_injection(uuid.uuid4(), trigger_phrase, is_investigation, False)

    return HookResult.empty()
