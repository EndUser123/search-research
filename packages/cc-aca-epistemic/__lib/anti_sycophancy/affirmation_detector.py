"""
Affirmation Detector v2.0 - Word boundary + LLM self-prompt approach.

PRINCIPLE: The LLM knows if it started with praise to be agreeable or because
it genuinely advances the conversation. Ask it directly.

APPROACH:
1. Fast word boundary check (not brittle regex)
2. If praise detected, return match with self-assessment prompt
3. Let the LLM honestly evaluate its own intent

Usage:
    from anti_sycophancy.affirmation_detector import detect_praise_opener
    
    result = detect_praise_opener(response_text)
    if result:
        # Inject result.self_prompt into response
"""

import re
from typing import NamedTuple, Optional, Set

__all__ = ["detect_praise_opener", "PraiseMatch", "detect_affirmation"]


class PraiseMatch(NamedTuple):
    """Detection result with self-assessment prompt."""
    matched: str        # The detected opener phrase
    category: str       # Type: "praise", "agreement", "flattery"
    self_prompt: str    # LLM self-assessment questions


# Word sets for fast boundary detection
PRAISE_STARTERS: Set[str] = {
    'great', 'excellent', 'wonderful', 'fantastic', 'brilliant',
    'perfect', 'amazing', 'awesome', 'outstanding', 'superb',
    'terrific', 'marvelous', 'splendid'
}

AGREEMENT_STARTERS: Set[str] = {
    'right', 'correct', 'exactly', 'absolutely', 'precisely',
    'indeed', 'definitely', 'certainly'
}

FLATTERY_PHRASES: Set[str] = {
    'good job', 'nice job', 'great job', 'well done',
    'good catch', 'nice catch', 'great catch',
    'good point', 'great point', 'excellent point',
    'good question', 'great question', 'excellent question',
    'good observation', 'great observation', 'excellent observation',
    'good thinking', 'great thinking'
}

# Phrases that START with "you" and affirm the person
YOU_AFFIRMATIONS: Set[str] = {
    "you're right", "you are right", "you're correct", "you are correct",
    "you're absolutely right", "you are absolutely right",
    "you're totally right", "you are totally right"
}

# Phrases starting with "that's/that is" affirming correctness
THAT_AFFIRMATIONS: Set[str] = {
    "that's right", "that is right", "that's correct", "that is correct",
    "that's a great", "that is a great", "that's an excellent", "that is an excellent"
}


def _normalize(text: str) -> str:
    """Normalize text for matching: lowercase, strip markdown, collapse whitespace."""
    # Strip markdown bullets/asterisks
    text = re.sub(r'^[●•\*\-\s]+', '', text)
    # Collapse whitespace
    text = ' '.join(text.lower().split())
    return text


def _extract_opener(text: str, max_words: int = 6) -> tuple[str, list[str]]:
    """Extract first N words as opener for analysis."""
    normalized = _normalize(text)
    words = normalized.split()[:max_words]
    opener = ' '.join(words)
    return opener, words


def _check_praise_starter(words: list[str]) -> Optional[str]:
    """Check if response starts with praise word."""
    if not words:
        return None
    first = words[0].strip('!.,?')
    if first in PRAISE_STARTERS:
        # Check for "great question", "excellent point" patterns
        if len(words) >= 2:
            second = words[1].strip('!.,?')
            phrase = f"{first} {second}"
            if phrase in FLATTERY_PHRASES or second in {'question', 'point', 'observation', 'job', 'catch', 'thinking'}:
                return phrase
        return first
    return None


def _check_flattery_phrase(opener: str) -> Optional[str]:
    """Check for multi-word flattery phrases."""
    for phrase in FLATTERY_PHRASES:
        if opener.startswith(phrase):
            return phrase
    return None


def _check_you_affirmation(opener: str) -> Optional[str]:
    """Check for 'you're right' style affirmations."""
    for phrase in YOU_AFFIRMATIONS:
        if opener.startswith(phrase):
            return phrase
    return None


def _check_that_affirmation(opener: str) -> Optional[str]:
    """Check for 'that's correct' style affirmations."""
    for phrase in THAT_AFFIRMATIONS:
        if opener.startswith(phrase):
            return phrase
    return None


def _check_agreement_starter(words: list[str], opener: str) -> Optional[str]:
    """Check for agreement words, but allow analytical continuations."""
    if not words:
        return None
    first = words[0].strip('!.,?')

    if first in AGREEMENT_STARTERS:
        # Allow analytical: "Exactly - the architecture shows..."
        # Block sycophantic: "Exactly! I'll fix that."
        # Check for analytical continuation markers in first few words
        analytical_markers = {'the', 'this', 'that', 'because', 'since', 'as', 'when', 'if'}
        # Look at words 1-3 for analytical markers (skip punctuation)
        for word in words[1:4]:
            cleaned = word.strip('!.,?-—:')
            if cleaned in analytical_markers:
                return None  # Analytical, allow
            if cleaned and cleaned not in {'-', '—', ',', '.', ':', '!'}:
                # Found a real word that's not an analytical marker
                break
        return first
    return None


def _generate_self_prompt(matched: str, category: str) -> str:
    """Generate LLM self-assessment prompt based on detected pattern."""

    if category == "praise":
        return f'''
⚠️ SYCOPHANCY CHECK

Your response began with: "{matched}"

Answer honestly:
1. Did you start this way to be agreeable, or does it genuinely advance the conversation?
2. Would removing this opener change the helpfulness of your response?
3. Are you affirming the PERSON or engaging with the CONTENT?

If sycophantic (affirming person over content), restate without the praise opener.
Lead with substance, not flattery.
'''

    elif category == "agreement":
        return f'''
⚠️ SYCOPHANCY CHECK

Your response began with: "{matched}"

Answer honestly:
1. Did you verify this is correct, or are you agreeing to be agreeable?
2. If the user made an error, would you still have said "{matched}"?
3. What specific evidence supports your agreement?

If agreeing without verification, reframe: State what you verified and how.
Agreement should follow evidence, not precede it.
'''

    elif category == "flattery":
        return f'''
⚠️ SYCOPHANCY CHECK

Your response began with: "{matched}"

Answer honestly:
1. Does this praise add information, or is it social lubricant?
2. Would a direct, competent colleague say this, or just proceed to substance?
3. Are you managing the user's emotions rather than addressing their request?

CLAUDE.md FORBIDDEN: "Great question!", "Good job", "Excellent point"
These affirm the person rather than engage with content.

Restate: Drop the opener, lead with your actual response.
'''

    return ""


def detect_praise_opener(response: str) -> Optional[PraiseMatch]:
    """
    Detect sycophantic openers using word boundary matching.
    
    Returns PraiseMatch with self-assessment prompt if detected.
    Returns None if clean.
    
    Performance: ~10μs typical (word boundary, not regex)
    """
    if not response or len(response) < 3:
        return None

    opener, words = _extract_opener(response)

    # Check patterns in order of specificity

    # 1. Multi-word flattery phrases (most specific)
    matched = _check_flattery_phrase(opener)
    if matched:
        return PraiseMatch(
            matched=matched,
            category="flattery",
            self_prompt=_generate_self_prompt(matched, "flattery")
        )

    # 2. "You're right" affirmations
    matched = _check_you_affirmation(opener)
    if matched:
        return PraiseMatch(
            matched=matched,
            category="agreement",
            self_prompt=_generate_self_prompt(matched, "agreement")
        )

    # 3. "That's correct" affirmations
    matched = _check_that_affirmation(opener)
    if matched:
        return PraiseMatch(
            matched=matched,
            category="agreement",
            self_prompt=_generate_self_prompt(matched, "agreement")
        )

    # 4. Praise word starters (great, excellent, etc.)
    matched = _check_praise_starter(words)
    if matched:
        return PraiseMatch(
            matched=matched,
            category="praise",
            self_prompt=_generate_self_prompt(matched, "praise")
        )

    # 5. Agreement starters (exactly, absolutely, etc.)
    matched = _check_agreement_starter(words, opener)
    if matched:
        return PraiseMatch(
            matched=matched,
            category="agreement",
            self_prompt=_generate_self_prompt(matched, "agreement")
        )

    return None


# Legacy API compatibility
def detect_affirmation(response: str):
    """Legacy API - wraps detect_praise_opener for backward compatibility."""
    result = detect_praise_opener(response)
    if not result:
        return None

    # Convert to old format
    class AffirmationMatch(NamedTuple):
        matched: str
        suggestion: str
        severity: str

    return AffirmationMatch(
        matched=result.matched,
        suggestion=result.self_prompt.split('\n')[3] if result.self_prompt else "Remove sycophantic opener",
        severity="flag"  # All are flags now - LLM self-corrects
    )


# === Tests ===
if __name__ == "__main__":
    # Should detect (sycophantic)
    assert detect_praise_opener("Great question!") is not None, "Should catch 'Great question!'"
    assert detect_praise_opener("Excellent point!") is not None, "Should catch 'Excellent point!'"
    assert detect_praise_opener("Good catch! Let me look...") is not None
    assert detect_praise_opener("You're right.") is not None
    assert detect_praise_opener("You're right, I should check...") is not None
    assert detect_praise_opener("That's correct, and I'll fix...") is not None
    assert detect_praise_opener("Absolutely! I'll do that.") is not None
    assert detect_praise_opener("Perfect! Let me update...") is not None
    assert detect_praise_opener("Wonderful observation!") is not None
    assert detect_praise_opener("● Great question!") is not None, "Should strip markdown"
    assert detect_praise_opener("* Good point!") is not None, "Should strip asterisk"

    # Should pass (analytical or clean)
    assert detect_praise_opener("Exactly - the architecture shows...") is None, "Analytical continuation"
    assert detect_praise_opener("The issue is in line 42.") is None
    assert detect_praise_opener("Correction: skills call code directly.") is None
    assert detect_praise_opener("Error acknowledged—checking now.") is None
    assert detect_praise_opener("") is None

    # Category checks
    praise = detect_praise_opener("Great question!")
    assert praise and praise.category == "flattery", f"Expected flattery, got {praise.category if praise else None}"

    agreement = detect_praise_opener("You're right.")
    assert agreement and agreement.category == "agreement"

    # Self-prompt should contain guidance
    result = detect_praise_opener("Excellent observation!")
    assert result and "SYCOPHANCY CHECK" in result.self_prompt
    assert "honestly" in result.self_prompt.lower()

    print("✅ All tests passed")
