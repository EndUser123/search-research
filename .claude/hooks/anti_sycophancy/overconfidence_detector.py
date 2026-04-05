"""
Overconfidence Detector - Catches unverified causal assertions and catastrophizing.

Detects patterns where the LLM makes confident causal claims without evidence:
- "This explains why..." (causal assertion)
- "This is why..." (causal assertion)
- "...is broken" (catastrophizing)
- "...completely fails" (catastrophizing)

PRINCIPLE: The LLM knows if it verified causation or just pattern-matched.
           It just doesn't say so unless caught.

Usage:
    from anti_sycophancy.overconfidence_detector import detect_overconfidence
    
    result = detect_overconfidence(response_text)
    if result:
        print(f"Detected: {result.pattern_type} -> {result.suggestion}")
"""

import re
from typing import List, NamedTuple, Optional

__all__ = ["detect_overconfidence", "OverconfidenceMatch"]


class OverconfidenceMatch(NamedTuple):
    """Detection result with remediation guidance."""
    matched: str           # The problematic phrase
    pattern_type: str      # "causal_assertion" | "catastrophizing" | "unverified_attribution"
    suggestion: str        # How to fix it
    severity: str          # "flag" (warn) or "block" (reject)


# === WORD SETS (structural detection, not brittle regex) ===

# Causal assertion without evidence - pattern-matching from error to cause
CAUSAL_WORDS = frozenset([
    "explains",      # "this explains why"
    "proves",        # "this proves that"
    "confirms",      # "this confirms"
    "demonstrates",  # "this demonstrates"
    "shows",         # "this shows that" (when followed by causation)
    "indicates",     # "this indicates"
    "reveals",       # "this reveals"
    "establishes",   # "this establishes"
])

CAUSAL_PHRASES = [
    r"\bthis\s+explains\b",
    r"\bwhich\s+explains\b",
    r"\bthat\s+explains\b",
    r"\bthis\s+is\s+why\b",
    r"\bthis\s+is\s+the\s+reason\b",
    r"\bthe\s+reason\s+is\b",
    r"\bcaused\s+by\b",
    r"\bbecause\s+of\s+this\b",
    r"\bdue\s+to\s+this\b",
    r"\bthis\s+proves\b",
    r"\bthis\s+indicates\b",
    r"\bthis\s+confirms\b",
    r"\bthis\s+demonstrates\b",
]

# Catastrophizing - absolute statements about system state
CATASTROPHE_PHRASES = [
    r"\bis\s+broken\b",
    r"\bare\s+broken\b",
    r"\bcompletely\s+fails\b",
    r"\bcompletely\s+broken\b",
    r"\btotally\s+fails\b",
    r"\btotally\s+broken\b",
    r"\bdoesn't\s+work\s+at\s+all\b",
    r"\bcan't\s+work\b",
    r"\bwill\s+never\s+work\b",
    r"\bis\s+unusable\b",
    r"\bis\s+fundamentally\s+flawed\b",
    r"\bthe\s+system\s+is\s+broken\b",
]

# Overconfident intensifiers - certainty without evidence
INTENSIFIER_PHRASES = [
    r"\bdefinitely\s+explains\b",
    r"\bdefinitely\s+proves\b",
    r"\bdefinitely\s+shows\b",
    r"\bdefinitely\s+indicates\b",
    r"\bdefinitely\s+appropriate\b",
    r"\bdefinitely\s+correct\b",
    r"\bdefinitely\s+the\s+(?:cause|reason|problem)\b",
    r"\bclearly\s+the\s+(?:cause|reason|problem)\b",
    r"\bobviously\s+the\s+(?:cause|reason|problem)\b",
]

# Unverified attribution - claiming to know root cause
ATTRIBUTION_PHRASES = [
    r"\bthe\s+root\s+cause\s+is\b",
    r"\bthe\s+underlying\s+issue\s+is\b",
    r"\bthe\s+real\s+problem\s+is\b",
    r"\bthe\s+actual\s+issue\s+is\b",
]

# Outcome attribution - claiming X caused/handled outcome without tracing
# Pattern: Testing X, Y happened, therefore X caused Y (post-hoc fallacy)
OUTCOME_ATTRIBUTION_PHRASES = [
    r"\bcorrectly\s+(?:blocked|handled|triggered|prevented|caught)\b",
    r"\bsuccessfully\s+(?:blocked|handled|triggered|prevented|caught)\b",
    r"\b(?:blocked|handled|triggered|prevented|caught)\s+by\b",
    r"\bis\s+responsible\s+for\b",
    r"\bis\s+(?:what|why)\s+(?:blocked|caused|triggered|prevented)\b",
    r"\bthe\s+\w+\s+(?:hook|gate|validator|checker)\s+(?:blocked|caught|prevented)\b",
]

# Evidence markers that make causal claims acceptable
# NOTE: Current mode is lenient (accepts any marker).
# Future: Add STRICT_EVIDENCE_MODE env var requiring explicit "[Tier X]:" format
# Rationale: Staged adoption - start lenient, tighten based on effectiveness data
EVIDENCE_MARKERS = frozenset([
    "tier 1", "tier 2", "tier1", "tier2",
    "verified", "confirmed by", "test output shows",
    "logs show", "execution shows", "evidence:",
    "[supported]", "[verified]",
])


# Compile patterns for efficiency
_CAUSAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CAUSAL_PHRASES]
_CATASTROPHE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CATASTROPHE_PHRASES]
_ATTRIBUTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ATTRIBUTION_PHRASES]
_INTENSIFIER_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INTENSIFIER_PHRASES]
_OUTCOME_ATTRIBUTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in OUTCOME_ATTRIBUTION_PHRASES]


def _has_evidence_marker(text: str) -> bool:
    """Check if text contains evidence tier citation."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in EVIDENCE_MARKERS)


def _find_pattern(text: str, patterns: List[re.Pattern]) -> Optional[re.Match]:
    """Find first matching pattern in text."""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match
    return None


def detect_overconfidence(response: str) -> Optional[OverconfidenceMatch]:
    """
    Detect overconfident assertions without evidence.
    
    Returns None if clean, OverconfidenceMatch if problematic.
    
    Strategy:
    1. Check for causal assertion patterns
    2. Check for catastrophizing patterns
    3. Check for unverified attribution
    4. If found, check if evidence marker present (makes it acceptable)
    """
    if not response:
        return None

    # Normalize whitespace for matching
    text = ' '.join(response.split())

    # 1. Check for causal assertions
    causal_match = _find_pattern(text, _CAUSAL_PATTERNS)
    if causal_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=causal_match.group(0),
            pattern_type="causal_assertion",
            suggestion="Add evidence tier: '[Tier X]: This explains...' or reframe as hypothesis: 'This MAY explain...'",
            severity="flag"
        )

    # 2. Check for catastrophizing
    catastrophe_match = _find_pattern(text, _CATASTROPHE_PATTERNS)
    if catastrophe_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=catastrophe_match.group(0),
            pattern_type="catastrophizing",
            suggestion="Specify scope: 'X functionality is not working' instead of 'system is broken'",
            severity="flag"
        )

    # 3. Check for unverified attribution (root cause claims)
    attribution_match = _find_pattern(text, _ATTRIBUTION_PATTERNS)
    if attribution_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=attribution_match.group(0),
            pattern_type="unverified_attribution",
            suggestion="Root cause claims require Tier 1/2 evidence. Add verification or use 'Hypothesis:' prefix",
            severity="flag"  # Could be "block" for high-stakes contexts
        )

    # 4. Check for overconfident intensifiers
    intensifier_match = _find_pattern(text, _INTENSIFIER_PATTERNS)
    if intensifier_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=intensifier_match.group(0),
            pattern_type="overconfident_intensifier",
            suggestion="'Definitely/clearly/obviously' claims need evidence. Remove intensifier or add tier citation",
            severity="flag"
        )

    # 5. Check for outcome attribution (post-hoc causation claims)
    outcome_match = _find_pattern(text, _OUTCOME_ATTRIBUTION_PATTERNS)
    if outcome_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=outcome_match.group(0),
            pattern_type="outcome_attribution",
            suggestion="Trace which component caused outcome (logs, hook output). Context ≠ causation. Use '[INFERRED]' if untraced",
            severity="flag"
        )

    return None


def detect_all_overconfidence(response: str) -> List[OverconfidenceMatch]:
    """
    Detect ALL overconfidence patterns (not just first).
    
    Useful for comprehensive analysis.
    """
    if not response:
        return []

    results = []
    text = ' '.join(response.split())
    has_evidence = _has_evidence_marker(text)

    if not has_evidence:
        # Collect all causal matches
        for pattern in _CAUSAL_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="causal_assertion",
                    suggestion="Add evidence tier or reframe as hypothesis",
                    severity="flag"
                ))

        # Collect all catastrophe matches
        for pattern in _CATASTROPHE_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="catastrophizing",
                    suggestion="Specify scope instead of absolute statements",
                    severity="flag"
                ))

        # Collect all attribution matches
        for pattern in _ATTRIBUTION_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="unverified_attribution",
                    suggestion="Root cause claims require evidence tier",
                    severity="flag"
                ))

        # Collect all intensifier matches
        for pattern in _INTENSIFIER_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="overconfident_intensifier",
                    suggestion="Remove intensifier or add evidence",
                    severity="flag"
                ))

        # Collect all outcome attribution matches
        for pattern in _OUTCOME_ATTRIBUTION_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="outcome_attribution",
                    suggestion="Trace which component caused outcome. Context ≠ causation",
                    severity="flag"
                ))

    return results


# === Inline tests (run with: python -m anti_sycophancy.overconfidence_detector) ===
if __name__ == "__main__":
    # Should detect (overconfident)
    assert detect_overconfidence("This explains why the tests failed") is not None
    assert detect_overconfidence("The system is broken") is not None
    assert detect_overconfidence("The root cause is the missing import") is not None
    assert detect_overconfidence("This is why the API returns errors") is not None
    assert detect_overconfidence("Due to this, everything fails") is not None
    assert detect_overconfidence("The code completely fails under load") is not None

    # Outcome attribution tests (post-hoc causation)
    assert detect_overconfidence("The hook correctly blocked the command") is not None
    assert detect_overconfidence("This was handled by the validator") is not None
    assert detect_overconfidence("The gate successfully prevented execution") is not None
    assert detect_overconfidence("blocked by the safety hook") is not None
    assert detect_overconfidence("The TDD hook caught the violation") is not None

    # Should pass (has evidence or acceptable)
    assert detect_overconfidence("[Tier 1]: This explains the failure") is None
    assert detect_overconfidence("Verified: The root cause is X") is None
    assert detect_overconfidence("Test output shows this is why it fails") is None
    assert detect_overconfidence("The import statement is missing") is None  # No causal claim
    assert detect_overconfidence("I need to investigate further") is None
    assert detect_overconfidence("") is None
    # Evidence markers make outcome attribution acceptable
    assert detect_overconfidence("Logs show: The hook correctly blocked it") is None
    assert detect_overconfidence("[Tier 1]: blocked by the safety hook") is None

    # Pattern type checks
    causal = detect_overconfidence("This explains the error")
    assert causal and causal.pattern_type == "causal_assertion"

    catastrophe = detect_overconfidence("The entire system is broken")
    assert catastrophe and catastrophe.pattern_type == "catastrophizing"

    attribution = detect_overconfidence("The root cause is the config")
    assert attribution and attribution.pattern_type == "unverified_attribution"

    outcome = detect_overconfidence("The hook correctly blocked the command")
    assert outcome and outcome.pattern_type == "outcome_attribution"

    # Multi-detection
    multi_text = "This explains why the system is broken. The root cause is X."
    all_matches = detect_all_overconfidence(multi_text)
    assert len(all_matches) >= 3, f"Expected 3+ matches, got {len(all_matches)}"

    # Multi-detection with outcome attribution
    multi_outcome = "The hook correctly blocked this. It was handled by the validator."
    outcome_matches = detect_all_overconfidence(multi_outcome)
    assert len(outcome_matches) >= 2, f"Expected 2+ outcome matches, got {len(outcome_matches)}"

    print("✅ All tests passed")
