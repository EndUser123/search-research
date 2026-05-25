#!/usr/bin/env python3
"""Response intent classification for Stop gates.

Classifies whether a response is:
- A first-person commitment to act (block target)
- A diagnostic/debug discussion about triggers (block skip)
- Neutral analysis or report

Used by approval and commit gates to avoid blocking meta-discussion.
"""
from __future__ import annotations

import re


def _strip_region(text: str, start: int, end: int) -> str:
    """Remove a region from text, replacing with spaces to preserve position."""
    if start < 0 or end > len(text) or start >= end:
        return text
    return text[:start] + " " * (end - start) + text[end:]


def _strip_code_blocks(text: str) -> str:
    """Remove fenced code blocks, handling Windows line endings."""
    # Normalize line endings
    text = text.replace("\r\n", "\n")
    # Remove fenced code blocks (```...```)
    while True:
        start = text.find("```")
        if start == -1:
            break
        end = text.find("```", start + 3)
        if end == -1:
            break
        text = _strip_region(text, start, end + 3)
    return text.strip()


def _strip_inline_elements(text: str) -> str:
    # DESIGN NOTE: QUOTE / META STRIPPING CONTRACT
    #
    # Purpose
    # This function strips *non-operative* text regions before pattern matching so that
    # meta discussion and examples do not trigger agreement / commitment gates.
    #
    # Covered regions
    # We treat the following as QUOTED/META and strip them:
    #   - Inline code         (`...`)
    #   - Straight ASCII quotes:  "..." and '...'
    #   - Curly Unicode quotes:
    #       "..." (U+201C / U+201D), '...' (U+2018 / U+2019)
    #   - Dollar-quoted spans: $...$
    #   - HTML entity-quoted spans:
    #       &quot;...&quot;, &apos;...&apos;, &#39;...&#39;
    #
    # Invariants
    #   - Only *paired* delimiters are stripped. Bare characters (a single curly
    #     apostrophe in I'll, a lone $, or a single &quot;) must remain intact.
    #   - Stripping a region removes the quoted content so that subsequent commitment
    #     pattern checks operate only on operative text.
    #
    # Why Unicode and entity forms are included
    # Real-world logs contain typographic quotes and entity-encoded quotes, so limiting
    # stripping to ASCII "..." / '...' left known false-positive paths. We normalize
    # these variants here so that only operative, unquoted agreement/commitment
    # language is visible to the gate.
    #
    # Risk boundary
    # The regexes are intentionally narrow:
    #   - Curly-quote patterns require matching open/close delimiters and exclude
    #     curly characters in the interior, so contractions with a single curly
    #     apostrophe do NOT match.
    #   - Dollar-quoted and entity-quoted patterns require both delimiters; bare $
    #     or entity tokens survive.
    #
    # If you modify this logic:
    #   - Update the corresponding tests in tests/test_response_intent.py
    #   - Re-run:  python -m pytest tests/test_response_intent.py -v
    #   - Do NOT simplify by dropping Unicode/entity handling or by broad "ignore
    #     weird text" heuristics; that reintroduces known faults.
    """Remove inline code, quotes, blockquotes, bullets from text."""
    # Inline code (must be done before double-quote stripping)
    text = re.sub(r"`[^`]*`", " ", text)
    # Double-quoted strings — straight ASCII
    text = re.sub(r'"[^"]*"', " ", text)
    # Single-quoted strings — straight ASCII
    text = re.sub(r"'[^']*'", " ", text)
    # Double-quoted strings — Unicode curly quotes
    text = re.sub(r'[“”][^“”]*[“”]', " ", text)
    # Single-quoted strings — Unicode curly quotes
    text = re.sub(r'[‘’][^‘’]*[‘’]', " ", text)
    # Dollar-quoted strings (LaTeX/math notation)
    text = re.sub(r"\$[^$]*\$", " ", text)
    # HTML entities for quotes
    text = re.sub(r"&quot;[^&]*&quot;", " ", text)
    text = re.sub(r"&apos;[^&]*&apos;", " ", text)
    text = re.sub(r"&#39;[^&#]*&#39;", " ", text)
    # Blockquote lines (lines starting with >)
    lines = text.split("\n")
    lines = [" " if re.match(r"^\s*>", line) else line for line in lines]
    text = "\n".join(lines)
    # Bullet points and numbered lists (full line match)
    lines = text.split("\n")
    lines = [
        " " if re.match(r"^\s*[-*]\s+", line) or re.match(r"^\s*\d+\.\s+", line) else line
        for line in lines
    ]
    text = "\n".join(lines)
    return text


# Meta/debug discussion patterns — discussion about triggers, not commitments
_META_PATTERNS = [
    re.compile(r"(?i)\b(?:the phrase|trigger|triggered|fired|blocked by)\b"),
    re.compile(r"(?i)\b(?:approval gate|commit gate)\b"),
    re.compile(r"(?i)\b(?:gate.*?pattern|gate pattern|match.*?pattern)\b"),
    re.compile(r"(?i)\b(?:show (?:me )?what text|which (?:phrase|word|pattern))\b"),
    re.compile(r"(?i)\b(?:want me to implement|proceeding to implement)\b.*\?"),
    re.compile(r"(?i)\b(?:can (?:you|i) (?:show|see|check|debug))\b"),
    re.compile(r"(?i)\b(?:i was|i'm|my) (?:blocked|triggered)\b"),
    re.compile(r"(?i)\b(?:IMPLEMENTATION(?: WITHOUT)?|APPROVAL)\b.*(?:blocked|gate|error)"),
    re.compile(r"(?i)\b(?:stop hook|stop.*block)\b.*(?:feedback|error|message)"),
    re.compile(r"(?i)^\s*(?:BLOCKED|BLOCK|ERROR):", re.MULTILINE),
    re.compile(r"(?i)\b(?:the phrase|word|text|string)\s+(?:that )?(?:triggered|fired|matched)\b"),
    re.compile(r"(?i)\b(?:command|phrase|text)\s+['\"]"),  # Discussion about commands/phrases
]

# First-person commitment patterns — these ARE action commitments
_COMMITMENT_PATTERNS = [
    # "I will implement" / "I will commit" / "I will execute" / "I will now X"
    re.compile(r"(?i)\bi\s+will\s+(?:now\s+)?(?:implement|execute|deploy|commit|push|merge|rebase)\b"),
    # "I am going to implement" / "I am going to commit"
    re.compile(r"(?i)\bi\s+am\s+(?:going\s+to\s+)?(?:implement|execute|deploy|commit|push|merge)\b"),
    # "let me implement/execute/commit"
    re.compile(r"(?i)\blet me\s+(?:proceed|implement|execute|commit)\b"),
    # "I am implementing now"
    re.compile(r"(?i)\bi\s+am\s+implement(?:ing|ed)\b"),
    # "Proceeding to implement" (standalone commitment)
    re.compile(r"(?i)^Proceeding\s+to\s+implement\b"),
    # "I am about to implement/commit"
    re.compile(r"(?i)\bi\s+am\s+(?:about\s+to|ready\s+to|just\s+about\s+to)\s+(?:implement|execute|commit)\b"),
]


class IntentClass:
    """Response intent classification result."""
    IMPLEMENTATION_COMMITMENT = "implementation_commitment"
    COMMIT_COMMITMENT = "commit_commitment"
    GATE_DEBUG_META = "gate_debug_meta"
    NEUTRAL_ANALYSIS = "neutral_analysis"
    COMPLETION_REPORT = "completion_report"


def _strip_quoted(text: str) -> str:
    """Remove quoted/metadata regions from text before pattern matching."""
    text = _strip_code_blocks(text)
    text = _strip_inline_elements(text)
    return text


def classify_response_intent(response: str, gate_name: str = "approval") -> str:
    """Classify the intent of a response for gate coordination.

    Args:
        response: The full response text from Stop.py
        gate_name: "approval" or "commit" to help with debug detection

    Returns:
        IntentClass value describing the response intent
    """
    if not response:
        return IntentClass.NEUTRAL_ANALYSIS

    response_lower = response.lower()

    # Strip quoted regions FIRST, then check commitments
    stripped = _strip_quoted(response)
    original_has_code_block = "```" in response

    # Check for direct commitments in non-quoted text (PRIMARY classification)
    if gate_name == "approval":
        for pat in _COMMITMENT_PATTERNS:
            if pat.search(stripped):
                return IntentClass.IMPLEMENTATION_COMMITMENT
    elif gate_name == "commit":
        commit_pat = re.compile(
            r"(?i)\bi\s+(?:will|am)\s+(?:now\s+)?(?:going\s+to\s+)?"
            r"(?:commit(?:ting|s)?|push(?:ing)?|merge|rebase|stage)\b"
        )
        if commit_pat.search(stripped):
            return IntentClass.COMMIT_COMMITMENT

    # No commitment found in stripped text — check if original has meta content
    # This handles: quoted trigger phrases, code blocks, bullets, blockquotes
    # Only classify as GATE_DEBUG_META when there's no real commitment

    # Check meta patterns on original (handles code blocks that were stripped to empty)
    for pat in _META_PATTERNS:
        if pat.search(response):
            return IntentClass.GATE_DEBUG_META

    # Stripped to empty after removing code blocks/bullets/blockquotes = meta context
    # These are text containing only trigger-like phrases in special markdown contexts
    if original_has_code_block and not stripped.strip():
        return IntentClass.GATE_DEBUG_META

    # Bullets and blockquotes stripped to empty also indicate meta context
    original_has_special_format = (
        original_has_code_block or
        re.search(r"^\s*[-*]\s+", response, re.MULTILINE) or
        re.search(r"^\s*>", response, re.MULTILINE)
    )
    if original_has_special_format and not stripped.strip():
        return IntentClass.GATE_DEBUG_META

    # Check for completion report markers
    completion_markers = ("tests passed", "pytest output", "all tests pass",
                          "implementation complete", "verification complete")
    if any(m in response_lower for m in completion_markers):
        return IntentClass.COMPLETION_REPORT

    # If no commitment pattern found after stripping quotes, treat as neutral
    return IntentClass.NEUTRAL_ANALYSIS


def is_meta_or_quoted_context(
    response: str, trigger_patterns: list[re.Pattern] | None = None
) -> bool:
    """Quick check: is this response discussing gates/triggers, not committing?

    Returns True if the response should NOT trigger a block even if trigger
    phrases appear in it.

    Args:
        response: The response text
        trigger_patterns: Optional list of regex patterns that would trigger the gate.
                       If provided, only skips blocking if trigger pattern matched
                       AND context is meta (not just a neutral mention).
    """
    if not trigger_patterns:
        # No trigger patterns means this is pure context check
        return classify_response_intent(response) == IntentClass.GATE_DEBUG_META

    # Check if any trigger pattern actually matched
    any_triggered = any(p.search(response) for p in trigger_patterns)
    if not any_triggered:
        # No trigger matched — nothing would have been blocked anyway
        return False

    # Trigger matched — now check if it's meta/debug context vs real commitment
    intent = classify_response_intent(response)
    return intent == IntentClass.GATE_DEBUG_META
