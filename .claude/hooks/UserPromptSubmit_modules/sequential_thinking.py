"""Sequential thinking trigger detection hook.

Detects complex/analytical intent in user prompts and creates state files for
sequential thinking sessions. Provides multi-terminal safety via terminal_id field.

Trigger patterns (intent-based — match naturally typed requests):
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
- RAM: ~90MB per terminal → ~100MB shared total
- Fallback chain: daemon IPC → direct SentenceTransformer → regex-only
- Threshold: >0.70 strong match (trigger), 0.50-0.70 partial (secondary signal)
"""

from __future__ import annotations

import re
import sys
import uuid
from pathlib import Path
from typing import Optional

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Ensure __lib is importable (hooks dir is already in sys.path via UserPromptSubmit.py)
_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from __lib.sequential_state import create_state  # noqa: E402
from UserPromptSubmit_modules.sequential_thinking_semantic_client import (
    compute_similarity,
)
from UserPromptSubmit_modules.tag_emission import emit_tag  # noqa: E402

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
#
# Hard floor (15 chars): Minimum length for any analytical phrase.
#   - "debug the code" = 14 chars (too short)
#   - "analyze code AB" = 15 chars (exactly at floor, blocked)
#   - Rationale: Below 15 chars, even analytical keywords are likely casual or
#     incomplete thoughts that don't warrant a multi-step thinking process.
#
# Soft floor (40 chars): Threshold for requiring 2+ signals (pattern + technical depth).
#   - "why does the connection timing out" = 36 chars (needs technical depth)
#   - "analyze this architecture for scalability" = 42 chars (single pattern sufficient)
#   - Rationale: Prompts between 15-40 chars are ambiguous - they might be genuine
#     analytical queries or casual questions. Requiring a technical indicator
#     (e.g., "error", "issue", "architecture") as a second signal filters false positives.
#
# These thresholds were calibrated against test cases in test_sequential_thinking_hooks.py
# and represent a balance between catching genuine analytical intent and avoiding noise.
_HARD_FLOOR = 15  # Never trigger below this
_SOFT_FLOOR = 30  # Require 2+ signals below this (lowered from 40 for question patterns)

# Invariant assertion: hard floor must be less than soft floor
assert _HARD_FLOOR < _SOFT_FLOOR, (
    f"HARD_FLOOR ({_HARD_FLOOR}) must be less than SOFT_FLOOR ({_SOFT_FLOOR})"
)

# Negative patterns that prevent triggering even if positive pattern matches
# These catch config values, trivial questions, and false positives
_NEGATIVE_PATTERNS = [
    r"debug\s*(?:mode|flag|level)\s*[:=]",  # "debug mode: true", "debug flag = 1"
    r"debug\s*(?:enabled|disabled|on|off)",  # "debug enabled", "debug off"
    r"how\s+(?:does|do)\s+(?:this|it)\s+look\b",  # "how does this look?" (trivial)
    r"what\s+does\s+(?:this|that|it)\s+do\b",  # "what does this do?" (often casual)
    r"^.{1,20}\?$",  # Very short questions ending with ?
]

# Technical depth indicators that signal genuine analytical intent
#
# OVER-MATCHING RISK: Some indicators are broad (e.g., "code", "load", "out")
# and may match non-analytical prompts like "show me the code" or "help me out".
# These are kept because:
#   1. They're used as a SECONDARY signal (pattern match is required first)
#   2. The negative patterns filter common false positives
#   3. Short prompts (<40 chars) require 2+ signals, reducing false triggers
#
# If false positives increase, consider:
#   - Removing overly generic terms ("out", "best", "works")
#   - Adding context requirements (e.g., require "code" + "analyze" together)
#   - Monitoring trigger logs for patterns to add to _NEGATIVE_PATTERNS
_TECHNICAL_INDICATORS = [
    "because",
    "issue",
    "problem",
    "error",
    "fails",
    "bug",
    "unexpected",
    "broken",
    "crash",
    "exception",
    "traceback",
    "incorrect",
    "wrong",
    "difference",
    "compare",
    "versus",
    "vs",
    "tradeoff",
    "alternative",
    "better",
    "optimize",
    "improve",
    "refactor",
    "architecture",
    "design",
    "pattern",
    # Additional indicators for short prompts that are genuinely analytical
    "code",
    "function",
    "module",
    "service",
    "api",
    "root",
    "cause",
    "risk",
    "security",
    "performance",
    "detail",
    "option",
    "approach",
    "method",
    # Strategy and efficiency indicators
    "strategy",
    "way",
    "efficient",
    "coupling",
    "scale",
    "scalable",
    "best",
    "works",
    "handles",
    "reduces",
    "edge case",
    "mechanism",
    # System and infrastructure indicators
    "load",
    "connection",
    "timing",
    "out",
    "timeout",
    "distributed",
    "database",
    "migration",
    "deadlock",
    "consistency",
    "flow",
    "leak",
    "memory",
    "intermittent",
    "limit",
    "rate",
    "safely",
    "profile",
    "concern",
    "inject",
    "dependency",
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
    # Interrogative patterns — questions are the natural trigger for "think before answering"
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


@register_hook("sequential_thinking", priority=8.5)
def sequential_thinking_hook(context: HookContext) -> HookResult:
    """Detect sequential thinking triggers and inject session context.

    Uses hybrid detection:
    1. Regex patterns (primary signal)
    2. Semantic similarity (secondary signal - boosts confidence for partial regex matches)
    3. Technical depth indicators (additional signal for short prompts)
    """
    # Skip skill invocations — they have their own explicit path
    if context.prompt.strip().startswith("/"):
        return HookResult.empty()

    prompt = context.prompt
    prompt_lower = prompt.lower()
    terminal_id = context.terminal_id or ""

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
        # If semantic detection fails, fall back to regex-only behavior
        semantic_triggered = False
        semantic_phrase = None

    # If neither regex nor semantic triggered, don't trigger
    if not matched_pattern and not semantic_triggered:
        return HookResult.empty()

    # Apply gating logic with combined signals
    # - Regex strong signal: pattern matched + gating passed
    # - Semantic boost: pattern matched + semantic partial match + gating passed
    # - Direct semantic: semantic strong match (bypasses gating for short prompts)
    prompt_len = len(prompt.strip())

    # Check negative patterns first (applies to all lengths)
    if _matches_negative_pattern(prompt):
        return HookResult.empty()

    # Hard floor: never trigger at 15 chars or below
    if prompt_len <= _HARD_FLOOR:
        return HookResult.empty()

    # Strong semantic match (>0.70) triggers directly - BUT still must pass hard floor
    # (hard floor already checked above at line 408-410)
    if semantic_triggered and not matched_pattern:
        # Direct semantic trigger - use semantic phrase
        # Hard floor already verified (line 408-410 runs before this branch)
        session_id = uuid.uuid4()
        trigger_phrase = semantic_phrase or "semantic similarity match"
        create_state(session_id, trigger_phrase, terminal_id)
        seq_tag = emit_tag("SEQ")
        tag_header = (
            f"{seq_tag}\n"
            f"**TAG EMISSION REQUIRED**: Begin your response with the [SEQ] tag above "
            f"to indicate active sequential reasoning mode.\n\n"
        )
        injection = (
            f"{tag_header}"
            f"<sequential_thinking>\n"
            f"Session ID: {session_id}\n"
            f"Trigger: {trigger_phrase}\n"
            f"Mode: initial (iteration 0 of 2)\n"
            f"</sequential_thinking>\n\n"
            f"I'll approach this step-by-step, then critically analyze my answer, "
            f"and finally improve my reasoning based on the critique.\n"
        )
        return HookResult(context=injection, tokens=200)

    # Above soft floor: single signal sufficient (regex OR semantic strong)
    if prompt_len >= _SOFT_FLOOR:
        if matched_pattern or semantic_triggered:
            session_id = uuid.uuid4()
            trigger_phrase = (
                _extract_trigger_phrase(prompt, matched_pattern)
                if matched_pattern
                else (semantic_phrase or "semantic similarity match")
            )
            create_state(session_id, trigger_phrase, terminal_id)
            seq_tag = emit_tag("SEQ")
            tag_header = (
                f"{seq_tag}\n"
                f"**TAG EMISSION REQUIRED**: Begin your response with the [SEQ] tag above "
                f"to indicate active sequential reasoning mode.\n\n"
            )
            injection = (
                f"{tag_header}"
                f"<sequential_thinking>\n"
                f"Session ID: {session_id}\n"
                f"Trigger: {trigger_phrase}\n"
                f"Mode: initial (iteration 0 of 2)\n"
                f"</sequential_thinking>\n\n"
                f"I'll approach this step-by-step, then critically analyze my answer, "
                f"and finally improve my reasoning based on the critique.\n"
            )
            return HookResult(context=injection, tokens=200)

    # Soft floor zone (15-30 chars): require 2+ signals
    # BUT semantic partial match does NOT help interrogatives - they need technical depth
    # Interrogatives (what/how/when/where/can/could/would/should) are casual questions
    # that shouldn't trigger just because they're semantically similar to an analytical question
    _INTERROGATIVE_KEYWORDS = [
        "should",
        "can",
        "could",
        "would",
        "what",
        "how",
        "why",
        "when",
        "where",
        "whether",
    ]

    def _is_interrogative_match() -> bool:
        """Check if matched pattern is an interrogative question pattern.

        Uses substring matching on the pattern string since we can't reliably use
        regex matching (pattern strings start with \\b which fails at string start).
        """
        if not matched_pattern:
            return False
        # Check if pattern string contains interrogative keywords as substrings
        pattern_lower = matched_pattern.lower()
        return any(kw in pattern_lower for kw in _INTERROGATIVE_KEYWORDS)

    signals = 0
    if matched_pattern:
        signals += 1
    if semantic_phrase and not _is_interrogative_match():
        # Semantic partial match only helps non-interrogatives
        # (interrogatives need technical depth to confirm analytical intent)
        signals += 1
    if _has_technical_depth(prompt):
        signals += 1

    if signals >= 2:
        session_id = uuid.uuid4()
        trigger_phrase = (
            _extract_trigger_phrase(prompt, matched_pattern)
            if matched_pattern
            else (semantic_phrase or "combined signals")
        )
        create_state(session_id, trigger_phrase, terminal_id)
        seq_tag = emit_tag("SEQ")
        tag_header = (
            f"{seq_tag}\n"
            f"**TAG EMISSION REQUIRED**: Begin your response with the [SEQ] tag above "
            f"to indicate active sequential reasoning mode.\n\n"
        )
        injection = (
            f"{tag_header}"
            f"<sequential_thinking>\n"
            f"Session ID: {session_id}\n"
            f"Trigger: {trigger_phrase}\n"
            f"Mode: initial (iteration 0 of 2)\n"
            f"</sequential_thinking>\n\n"
            f"I'll approach this step-by-step, then critically analyze my answer, "
            f"and finally improve my reasoning based on the critique.\n"
        )
        return HookResult(context=injection, tokens=200)

    return HookResult.empty()
