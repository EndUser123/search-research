"""
Unverified Stance Detector - catches doubt/skepticism about user claims without verification.

PRINCIPLE: Don't cast doubt on what the user says unless you've checked.
           "You're right to push back" and "Let me verify that" are both
           stances that require evidence. Without a tool call, they're empty.

Two failure modes caught:
1. Sycophantic doubt: "You're right to push back/question/be skeptical"
2. Empty hedging: "Let me verify that" / "That sounds high" (without actual verification)

Usage:
    from anti_sycophancy.unverified_stance_detector import detect_unverified_stance

    result = detect_unverified_stance(response_text, data)
    if result:
        # Inject result.self_prompt into response
"""

import re
from typing import NamedTuple

__all__ = ["detect_unverified_stance", "StanceMatch"]


class StanceMatch(NamedTuple):
    """Detection result with self-assessment prompt."""
    matched: str        # The detected phrase
    category: str       # "sycophantic_doubt" | "empty_hedge"
    self_prompt: str    # LLM self-assessment questions
    severity: str       # "warn" for now (not "block")


# SYCOPHANTIC_DOUBT patterns - "you're right to doubt"
SYCOPHANTIC_DOUBT_PATTERNS: set[str] = {
    "you're right to push back",
    "you're right to question",
    "you're right to be skeptical",
    "you're absolutely right to question",
    "good instinct to question",
}

# SYCOPHANCY_INVERSION patterns - apology followed by same failing approach
# Detects: "I apologize" + dismissal conclusion without new cited evidence
APOLOGY_PATTERNS: set[str] = {
    "i apologize",
    "i'm sorry",
    "you're right",
    "my apologies",
    "sorry about that",
}

DISMISSAL_CONCLUSION_PATTERNS: set[str] = {
    "not a bug",
    "no fix needed",
    "not broken",
    "currently functioning",
    "working correctly",
    "working as expected",
    "no action needed",
    "no changes needed",
    "appears to be working",
    "is functioning normally",
    "testing artifact",
    "diagnostic artifact",
}

# Evidence of new investigation (escape hatch for legitimate corrections)
NEW_EVIDENCE_PATTERNS = re.compile(
    r"(?:"
    r"i\s+re-?ran\s+your\s+(?:exact\s+)?steps|"
    r"here\s+(?:are|is)\s+the\s+(?:logs?|output|trace|error)|"
    r"reproducing\s+your\s+(?:exact\s+)?(?:steps|scenario|error)|"
    r"using\s+your\s+(?:exact\s+)?(?:reproduction|repro|command|invocation)|"
    r"following\s+your\s+(?:exact\s+)?steps|"
    # Broader evidence: citing specific new investigation results
    r"after\s+(?:checking|investigating|tracing|reading)\s+(?:the|your)|"
    r"the\s+(?:actual|root)\s+cause\s+(?:is|was|turns\s+out)|"
    r"i\s+(?:found|discovered|confirmed)\s+that\s+(?:the|your)|"
    r"(?:the\s+)?(?:stack\s+)?trace\s+shows|"
    r"(?:line|file)\s+\d+\s+(?:shows?|reveals?|indicates?)"
    r")",
    re.IGNORECASE,
)

# EMPTY_HEDGE patterns - "let me check" without checking
EMPTY_HEDGE_PATTERNS: set[str] = {
    "let me verify",
    "let me double-check",
    "let me check on that",
    "that sounds high",
    "that sounds low",
    "that sounds unlikely",
    "i'm not sure that's accurate",
    "i doubt that",
    "i can't confirm",
}

# Factual claim indicators (quantities, adoption, capabilities)
FACTUAL_INDICATORS: set[str] = {
    # Quantities
    "millions", "thousands", "hundreds", "100k", "200k", "500k", "1m", "2m",
    # Numbers (will catch in regex)
    # Adoption language (scoped to avoid false positives like "file has a bug")
    "used by", "stars", "popular", "widely", "adoption", "users",
    # Capability claims
    "supports", "integrates with", "can do", "able to", "capable of",
    # Negation words (for negative claims)
    "isn't", "doesn't", "won't", "can't", "never", "rarely", "hardly",
}

# Verification tools that count as evidence
VERIFICATION_TOOLS: set[str] = {"WebSearch", "WebFetch", "Bash"}


def _normalize(text: str) -> str:
    """Normalize text for matching: lowercase, collapse whitespace."""
    text = ' '.join(text.lower().split())
    return text


def _extract_tools_used(data: dict) -> set[str]:
    """Extract tool names from hook data."""
    tools = set()
    for tool in data.get("tools_used", []):
        name = tool.get("name", "") if isinstance(tool, dict) else str(tool)
        if name:
            tools.add(name)
    return tools


def _extract_user_message(data: dict) -> str:
    """Extract last user message from transcript."""
    transcript = data.get("transcript", [])
    if not transcript:
        return ""

    for entry in reversed(transcript):
        if entry.get("role") == "user":
            content = entry.get("content", "")
            if isinstance(content, list):
                # Handle list content (e.g., from multimodal inputs)
                user_msg = " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict)
                )
            else:
                user_msg = str(content)

            if user_msg:
                return user_msg

    return ""


def _has_factual_claim(text: str) -> bool:
    """Check if text contains factual claim indicators (excludes questions)."""
    normalized = _normalize(text)

    # Skip questions - they're not claims
    # Questions start with: who, what, when, where, why, how, which, do, does, can, could, would, should, is, are
    # Or end with ?
    words = normalized.split()
    if '?' in text or (words and words[0] in ('how', 'what', 'when', 'where', 'why', 'who', 'which', 'do', 'does', 'can', 'could', 'would', 'should', 'is', 'are')):
        return False

    # Check for "I think" - opinion, not factual claim
    if normalized.startswith('i think') or normalized.startswith('i believe'):
        return False

    # Check for factual indicator words
    for indicator in FACTUAL_INDICATORS:
        if indicator in normalized:
            return True

    # Check for numbers (digits or written out)
    # Pattern: "145k", "1.5 million", "100000", etc.
    if re.search(r'\b\d+[kmb]?\b', normalized):
        return True

    return False


def _strip_quoted_and_hook_blocks(text: str) -> str:
    """Remove Stop-hook artifacts and quoted blocks that aren't the LLM's own words.

    Strips:
    - Stop-hook feedback blocks (after 'Stop hook', 'Stop says:', etc.)
    - Markdown blockquotes (lines starting with '> ')
    - system-reminder blocks
    """
    lines = text.split("\n")
    result: list[str] = []
    skip = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("> "):
            continue

        if stripped.startswith("<system-reminder"):
            # Opening tag — start skipping content
            skip = True
            continue
        if stripped == "</system-reminder>":
            # Closing tag — stop skipping, process this line normally
            skip = False
            # Fall through to process this line (not a content line, will be skipped by final else or hook pattern check)
        if skip:
            continue

        if re.match(
            r"(?:Stop (?:hook|says)|⎿|Stop\s+hook\s+feedback|LAZY WORKAROUND|EPISTEMIC|"
            r"Pattern matched:|Required approach:|Remember:|This suggests|"
            r"⛔|⚠️|✅|❌|Block message:|Warning:)",
            stripped,
        ):
            skip = True
            continue

        result.append(line)

    return "\n".join(result)


def _has_concessive_clause(text: str) -> bool:
    """Detect if text contains a concessive subordinate clause before the target phrase.

    Matches patterns like:
    - "although I apologize... not a bug" (concessive before apology)
    - "even though it seems... not broken" (concessive before dismissal)
    - "while I understand... working correctly" (concessive before claim)
    """
    CONCESSIVE_BEFORE = re.compile(
        r"(?:although|even though|while|despite|notwithstanding|albeit)"
        r"\s+.{0,80}",
        re.IGNORECASE | re.DOTALL,
    )
    return bool(CONCESSIVE_BEFORE.search(text))


def _check_sycophancy_inversion(response: str) -> str | None:
    """Check for sycophancy inversion: apology + same dismissal conclusion.

    Detects the pattern where the AI apologizes after user pushback but then
    reaches the same dismissive conclusion (e.g., "I apologize... NOT A BUG").

    Escape hatches:
    - Stop-hook artifacts are stripped before checking (self-referential loop fix)
    - Concessive subordinate clauses are excluded ("although I apologize...")
    - Evidence of new investigation (NEW_EVIDENCE_PATTERNS) bypasses the gate
    """
    clean = _strip_quoted_and_hook_blocks(response)
    normalized = _normalize(clean)

    has_apology = any(pattern in normalized for pattern in APOLOGY_PATTERNS)
    if not has_apology:
        return None

    # Concessive clause: "although I apologize..." — allow
    if _has_concessive_clause(normalized):
        return None

    has_dismissal = None
    for pattern in DISMISSAL_CONCLUSION_PATTERNS:
        if pattern in normalized:
            has_dismissal = pattern
            break

    if not has_dismissal:
        return None

    # Escape hatch: new evidence clearly referenced (user's exact steps)
    if NEW_EVIDENCE_PATTERNS.search(response):
        return None

    return f"apology + dismissal: '{has_dismissal}'"


def _check_sycophantic_doubt(response: str) -> str | None:
    """Check for sycophantic doubt patterns."""
    normalized = _normalize(response)

    for pattern in SYCOPHANTIC_DOUBT_PATTERNS:
        if pattern in normalized:
            return pattern

    return None


def _check_empty_hedge(response: str) -> str | None:
    """Check for empty hedge patterns."""
    normalized = _normalize(response)

    for pattern in EMPTY_HEDGE_PATTERNS:
        if pattern in normalized:
            return pattern

    return None


def _generate_self_prompt(matched: str) -> str:
    """Generate LLM self-assessment prompt based on detected pattern."""

    base_prompt = f"""⚠️ UNVERIFIED STANCE CHECK

Your response contains: "{matched}"

But you used no verification tools (WebSearch, WebFetch) this turn.

1. Did you actually check this claim, or are you hedging to seem careful?
2. If you don't know, say "I don't know" — don't imply the user is wrong.
3. If you want to verify, actually call WebSearch/WebFetch first.

The user's claim may be correct. Don't cast doubt without evidence."""

    return base_prompt


def _generate_inversion_prompt(matched: str) -> str:
    """Generate self-assessment prompt for sycophancy inversion detection."""
    return f"""⚠️ SYCOPHANCY INVERSION DETECTED

Your response contains: {matched}

You apologized but then reached the SAME dismissive conclusion. This is worse
than not apologizing — it signals you heard the user but still won't investigate.

Before concluding "not a bug" / "working correctly" after user pushback:
1. Did you reproduce the EXACT failure the user reported, using THEIR steps?
2. Did you test the FAILING path, or only the PASSING path?
3. If you generated the error yourself during diagnostics, that error IS real.
   A reproducible error is not a "testing artifact."

If you can't reproduce the user's failure path: say so explicitly and ask for
their exact reproduction steps. Do NOT declare "no fix needed." """


def detect_unverified_stance(response: str, data: dict) -> StanceMatch | None:
    """
    Detect unverified stance (doubt/hedging without verification).

    Returns StanceMatch with self-assessment prompt if detected.
    Returns None if clean or verification tools were used.

    Detection logic:
    1. Extract tools_used from data
    2. Extract user message from transcript
    3. Check if user made factual claim
    4. Check if response has sycophantic doubt or empty hedge
    5. Return match only if ALL conditions met AND no verification tools used
    """
    if not response or len(response) < 3:
        return None

    # Check for sycophancy inversion FIRST (apology + same conclusion)
    # This fires regardless of verification tools or factual claims because
    # the failure mode is: apologize then double down on the same approach
    inversion = _check_sycophancy_inversion(response)
    if inversion:
        return StanceMatch(
            matched=inversion,
            category="sycophancy_inversion",
            self_prompt=_generate_inversion_prompt(inversion),
            severity="warn",
        )

    # Check if verification tools were used
    tools_used = _extract_tools_used(data)
    if tools_used & VERIFICATION_TOOLS:
        # Verification was used, allow the stance
        return None

    # Extract user message
    user_msg = _extract_user_message(data)
    if not user_msg:
        # No user message, can't detect factual claim
        return None

    # Check if user made a factual claim
    if not _has_factual_claim(user_msg):
        # User didn't make factual claim, allow the stance
        return None

    # Check for sycophantic doubt patterns
    matched = _check_sycophantic_doubt(response)
    if matched:
        return StanceMatch(
            matched=matched,
            category="sycophantic_doubt",
            self_prompt=_generate_self_prompt(matched),
            severity="warn"
        )

    # Check for empty hedge patterns
    matched = _check_empty_hedge(response)
    if matched:
        return StanceMatch(
            matched=matched,
            category="empty_hedge",
            self_prompt=_generate_self_prompt(matched),
            severity="warn"
        )

    return None


# === Tests ===
if __name__ == "__main__":
    # Should detect (no verification tool used)

    # 1. OpenClaw case - sycophantic doubt
    data1 = {
        "response": "You're right to push back on that. Let me verify OpenClaw's actual adoption.",
        "transcript": [{"role": "user", "content": "I heard that OpenClaw is used by millions of solo people."}],
        "tools_used": [],
    }
    result1 = detect_unverified_stance(data1["response"], data1)
    assert result1 is not None, "Should detect sycophantic doubt"
    assert result1.category == "sycophantic_doubt"

    # 2. Empty hedge
    data2 = {
        "response": "That sounds high, let me verify that number.",
        "transcript": [{"role": "user", "content": "PyTorch has over 100k stars on GitHub."}],
        "tools_used": [],
    }
    result2 = detect_unverified_stance(data2["response"], data2)
    assert result2 is not None, "Should detect empty hedge"
    assert result2.category == "empty_hedge"

    # 3. "I doubt that" without checking
    data3 = {
        "response": "I doubt that's accurate. The number seems inflated.",
        "transcript": [{"role": "user", "content": "OpenClaw has 145k GitHub stars."}],
        "tools_used": [],
    }
    result3 = detect_unverified_stance(data3["response"], data3)
    assert result3 is not None, "Should detect doubt"

    # 4. Negative factual claim with hedge
    data4 = {
        "response": "I doubt that's true. OpenClaw isn't that popular.",
        "transcript": [{"role": "user", "content": "OpenClaw has 145k stars."}],
        "tools_used": [],
    }
    result4 = detect_unverified_stance(data4["response"], data4)
    assert result4 is not None, "Should detect negative claim + doubt"

    # 5. Multiple sycophantic doubt phrases
    data5 = {
        "response": "You're right to be skeptical. That sounds unlikely.",
        "transcript": [{"role": "user", "content": "I heard OpenClaw has billions of users."}],
        "tools_used": [],
    }
    result5 = detect_unverified_stance(data5["response"], data5)
    assert result5 is not None, "Should detect compound phrases"

    # Should NOT detect (verification tool was used)

    # 6. Hedge followed by actual verification
    data6 = {
        "response": "Let me verify that number.",
        "transcript": [{"role": "user", "content": "React has 200k stars."}],
        "tools_used": [{"name": "WebSearch"}],
    }
    result6 = detect_unverified_stance(data6["response"], data6)
    assert result6 is None, "Should allow when WebSearch used"

    # 7. Bash counts as verification
    data7 = {
        "response": "Let me verify those stars.",
        "transcript": [{"role": "user", "content": "React has 200k stars."}],
        "tools_used": [{"name": "Bash"}],
    }
    result7 = detect_unverified_stance(data7["response"], data7)
    assert result7 is None, "Should allow when Bash used"

    # Should NOT detect (not a factual claim)

    # 8. User asking a question
    data8 = {
        "response": "Let me check on that for you.",
        "transcript": [{"role": "user", "content": "How many stars does React have?"}],
        "tools_used": [],
    }
    result8 = detect_unverified_stance(data8["response"], data8)
    assert result8 is None, "Should allow when user asks question"

    # 9. User making subjective statement
    data9 = {
        "response": "You're right to question that approach.",
        "transcript": [{"role": "user", "content": "I think we should use a different architecture."}],
        "tools_used": [],
    }
    result9 = detect_unverified_stance(data9["response"], data9)
    assert result9 is None, "Should allow subjective statements"

    # Self-prompt should contain guidance
    result = detect_unverified_stance(
        "You're right to push back on that.",
        {"transcript": [{"role": "user", "content": "OpenClaw has millions of users."}], "tools_used": []}
    )
    assert result and "UNVERIFIED STANCE CHECK" in result.self_prompt
    assert "verification tools" in result.self_prompt.lower()

    print("✅ All tests passed")
