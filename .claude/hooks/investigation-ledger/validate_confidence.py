"""
Confidence Validator - Hardened Implementation
Ensures confidence claims don't exceed the investigation-based ceiling.

Addresses critique concerns:
- Mixed hedging detection (handles "might work, definitely processes")
- Improved verbal confidence detection
- Clear threshold logic
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Import ledger (same directory)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import calculate_confidence_ceiling, get_investigation_stats

# === Confidence Word Mappings ===

HIGH_CONFIDENCE_WORDS = {
    # 90%+ implied - only match self-assertions, not quoted/meta usage
    "i am certain": 90,
    "i'm certain": 90,
    "i am confident": 90,
    "i'm confident": 90,
    "definitely the": 90,
    "absolutely the": 90,
    "clearly the": 90,
    "obviously the": 90,
    "undoubtedly": 90,
    "without doubt": 90,
    "guaranteed to": 95,
    "100% confident": 100,
    "100% certain": 100,

    # 80-89% implied
    "highly likely": 85,
    "very likely": 85,
    "strongly believe": 85,
}

MEDIUM_CONFIDENCE_WORDS = {
    # 60-79% implied
    "likely": 70,
    "probably": 70,
    "most likely": 75,
    "should": 70,
    "expect": 70,
    "appears to": 65,
    "seems to": 65,
}

LOW_CONFIDENCE_WORDS = {
    # <60% implied (hedged, acceptable at any ceiling)
    "might": 50,
    "may": 50,
    "could": 50,
    "possibly": 50,
    "perhaps": 50,
    "uncertain": 40,
    "unsure": 40,
    "not sure": 40,
    "don't know": 30,
}

# Explicit confidence patterns
EXPLICIT_CONFIDENCE_PATTERN = re.compile(
    r'(\d{1,3})\s*%\s*(?:confident|confidence|certain|sure)',
    re.IGNORECASE
)

TIER_REFERENCE_PATTERN = re.compile(
    r'(?:tier\s*)?([1-4])\s*(?:evidence|confidence)',
    re.IGNORECASE
)


def _extract_explicit_confidence(text: str) -> List[Tuple[str, int]]:
    """
    Extract explicit confidence claims like "90% confident".
    Returns list of (matched_text, confidence_level).
    """
    results = []

    # Percentage patterns
    for match in EXPLICIT_CONFIDENCE_PATTERN.finditer(text):
        level = int(match.group(1))
        results.append((match.group(0), min(100, max(0, level))))

    # Tier references (Tier 1 = 95%, Tier 2 = 85%, Tier 3 = 75%, Tier 4 = 50%)
    tier_ceilings = {1: 95, 2: 85, 3: 75, 4: 50}
    for match in TIER_REFERENCE_PATTERN.finditer(text):
        tier = int(match.group(1))
        if tier in tier_ceilings:
            results.append((match.group(0), tier_ceilings[tier]))

    return results


def _extract_verbal_confidence(text: str) -> List[Tuple[str, int]]:
    """
    Extract verbal confidence markers.
    Returns list of (matched_text, implied_confidence).

    Skip matches inside:
    - Code blocks (``` ... ```)
    - Inline code (` ... `)
    - Quoted text (" ... " or ' ... ')
    - Error messages being quoted
    """
    results = []

    # Strip out code blocks, inline code, and quoted text before scanning
    clean_text = re.sub(r'```[\s\S]*?```', ' [CODE] ', text)
    clean_text = re.sub(r'`[^`]+`', ' [CODE] ', clean_text)
    clean_text = re.sub(r'"[^"]{10,}"', ' [QUOTE] ', clean_text)  # Long quotes
    clean_text = re.sub(r"'[^']{10,}'", ' [QUOTE] ', clean_text)
    # Remove lines that look like error output
    clean_text = re.sub(r'^.*(?:error|Error|ERROR):.*$', '', clean_text, flags=re.MULTILINE)
    clean_text = re.sub(r'^.*⛔.*$', '', clean_text, flags=re.MULTILINE)  # Hook error lines

    text_lower = clean_text.lower()

    # Check high confidence words (now require specific phrasing)
    for word, level in HIGH_CONFIDENCE_WORDS.items():
        if word in text_lower:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            for match in pattern.finditer(clean_text):
                results.append((match.group(0), level))

    # Check medium confidence words
    for word, level in MEDIUM_CONFIDENCE_WORDS.items():
        if word in text_lower:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            for match in pattern.finditer(clean_text):
                results.append((match.group(0), level))

    return results


def _detect_unhedged_assertions(text: str) -> bool:
    """
    Detect unhedged factual assertions that imply high confidence.

    Only triggers for specific patterns of declarative statements about
    system behavior without hedging language. Conservative to avoid
    false positives on normal descriptive text.
    """
    # Check if text contains hedging words
    hedge_words = [
        "might", "may", "could", "possibly", "perhaps", "uncertain",
        "unsure", "not sure", "don't know", "appears", "seems",
        "likely", "probably", "should", "expect", "typically",
        "usually", "generally", "normally"
    ]
    text_lower = text.lower()
    for hedge in hedge_words:
        if hedge in text_lower:
            return False  # Has hedging, not an unhedged assertion

    # Count declarative statements about system behavior
    declarative_verbs = [
        "validates", "validating", "handles", "handling", "processes", "processing",
        "manages", "managing", "creates", "creating", "generates", "generating",
        "dispatches", "dispatching", "ensures", "guarantees", "implements"
    ]

    sentences = text.split('.')
    declarative_count = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Check if sentence contains declarative verb without hedge
        for verb in declarative_verbs:
            if verb in s.lower():
                declarative_count += 1
                break

    # If 2+ declarative sentences without hedging, consider it unhedged assertion
    return declarative_count >= 2


def _get_max_confidence_in_text(text: str) -> Tuple[int, str]:
    """
    Get the maximum confidence level expressed in the text.
    Returns (max_level, source_description).
    """
    max_level = 0
    source = "none"

    # Check explicit confidence
    explicit = _extract_explicit_confidence(text)
    for matched, level in explicit:
        if level > max_level:
            max_level = level
            source = f"explicit: '{matched}'"

    # Check verbal confidence
    verbal = _extract_verbal_confidence(text)
    for matched, level in verbal:
        if level > max_level:
            max_level = level
            source = f"verbal: '{matched}'"

    # Check unhedged assertions (implies ~70% - allows Tier 3)
    if max_level < 70 and _detect_unhedged_assertions(text):
        max_level = 70
        source = "unhedged factual assertion"

    return (max_level, source)


def validate_confidence(response_text: str) -> Dict:
    """
    Validate that confidence claims don't exceed the investigation-based ceiling.
    
    Returns:
        {"valid": bool, "message": str|None, "details": dict}
    """
    # Skip very short responses
    if len(response_text) < 50:
        return {
            "valid": True,
            "message": None,
            "details": {"reason": "Short response (< 50 chars)"}
        }

    # Get ceiling based on investigation
    ceiling_info = calculate_confidence_ceiling()
    ceiling = ceiling_info["ceiling"]

    # Special case: zero ceiling means no claims allowed
    # But we need to allow questions and meta-responses
    if ceiling == 0:
        # Check if this is just a question or request for guidance
        if response_text.strip().endswith('?'):
            return {
                "valid": True,
                "message": None,
                "details": {"reason": "Response is a question"}
            }

        # Check if asking what to investigate
        investigation_phrases = [
            "what files", "which files", "should i read", "let me read",
            "i'll check", "i need to", "first, i should", "let me look"
        ]
        if any(phrase in response_text.lower() for phrase in investigation_phrases):
            return {
                "valid": True,
                "message": None,
                "details": {"reason": "Response indicates intent to investigate"}
            }

    # Get max confidence in response
    max_confidence, confidence_source = _get_max_confidence_in_text(response_text)

    # Validate against ceiling
    if max_confidence > ceiling:
        stats = get_investigation_stats()

        return {
            "valid": False,
            "message": f"⛔ CONFIDENCE EXCEEDS EVIDENCE\n\nYou expressed {max_confidence}% confidence ({confidence_source})\nBut your investigation only supports {ceiling}% ({ceiling_info['reason']})\n\nEither:\n1. Investigate more to raise your ceiling\n2. Hedge your claims appropriately",
            "details": {
                "max_confidence_found": max_confidence,
                "confidence_source": confidence_source,
                "ceiling": ceiling,
                "ceiling_reason": ceiling_info["reason"],
                "investigation_stats": stats
            }
        }

    return {
        "valid": True,
        "message": None,
        "details": {
            "max_confidence_found": max_confidence,
            "ceiling": ceiling,
            "headroom": ceiling - max_confidence
        }
    }


# === CLI for testing ===

if __name__ == "__main__":
    # Test mode: validate text from stdin or argument
    if len(sys.argv) > 1:
        test_text = " ".join(sys.argv[1:])
    else:
        test_text = sys.stdin.read()

    result = validate_confidence(test_text)
    print(json.dumps(result, indent=2))
