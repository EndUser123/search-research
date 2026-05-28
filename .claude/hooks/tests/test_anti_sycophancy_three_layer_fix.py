#!/usr/bin/env python3
"""
Comprehensive tests for the three-layer sycophancy fix.

Layer 1: Investigative challenge detection (UserPromptSubmit advocate injection)
Layer 2: Widened capitulation patterns (Stop hook detection)
Layer 3: Quoted-content exemption (false positive prevention)

Tests verify:
- New investigative challenge patterns catch missed RCA cases
- Widened capitulation patterns detect "You're right" variants
- Quoted-content exemption prevents false positives from transcript citations
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# Add plugin paths FIRST (so plugin modules take precedence over local hooks)
EPISTEMIC_PLUGIN = Path("P:/packages/cc-aca-epistemic")
EPISTEMIC_LIB = EPISTEMIC_PLUGIN / "__lib"
EPISTEMIC_HOOKS_UPS = EPISTEMIC_PLUGIN / "hooks" / "userpromptsubmit"

if EPISTEMIC_LIB.exists():
    sys.path.insert(0, str(EPISTEMIC_LIB))
if EPISTEMIC_HOOKS_UPS.exists():
    sys.path.insert(0, str(EPISTEMIC_HOOKS_UPS))

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from anti_sycophancy_injector import (
    HIGH_STAKES_PATTERNS,
    HIGH_STAKES_REGEX,
    _classify_prompt,
)
from anti_sycophancy.lazy_closure_detector import (
    SYCOPHANCY_CAPITULATION_PHRASES,
    _is_inside_quoted_content,
)


# ---------------------------------------------------------------------------
# Layer 1: Investigative Challenge Detection Tests
# ---------------------------------------------------------------------------

class TestLayer1InvestigativeChallenges:
    """Layer 1: Verify new HIGH_STAKES_PATTERNS catch investigative challenges."""

    @pytest.mark.parametrize("pattern", [
        r"did\s+you\s+(?:actually\s+)?(?:check|verify|run|test|sync|validate|confirm|look\s+at)",
        r"why\s+(?:is|are|was|were)\s+.+?\s+(?:the\s+)?(?:best|right|correct|optimal|necessary|only)\b",
        r"(?:is|are)\s+(?:this|that|it|you)\s+(?:really\s+|truly\s+|actually\s+)?(?:the\s+)?(?:best|right|correct|only)\s+(?:way|choice|approach|option|solution)",
        r"what\s+makes\s+(?:this|that|it)\s+(?:the\s+)?(?:best|right|correct)",
        r"how\s+do\s+you\s+know\s+(?:that|this|it)",
    ])
    def test_new_patterns_exist_in_high_stakes(self, pattern: str) -> None:
        """Verify all new investigative patterns are in HIGH_STAKES_PATTERNS."""
        assert pattern in HIGH_STAKES_PATTERNS, f"Pattern {pattern!r} not found in HIGH_STAKES_PATTERNS"

    def test_new_patterns_compiled_to_regex(self) -> None:
        """Verify new patterns are compiled and functional."""
        # Should have same number of compiled regex as source patterns
        assert len(HIGH_STAKES_REGEX) == len(HIGH_STAKES_PATTERNS)

    @pytest.mark.parametrize("challenge,expected", [
        # Pattern 1: did you check/verify/run/test/sync/validate/confirm/look at
        ("did you actually check that before claiming it works?", "high"),
        ("did you verify the cache was nuked correctly?", "high"),
        ("did you run the command to confirm?", "high"),
        ("did you test this behavior?", "high"),
        ("did you sync the right way?", "high"),
        ("did you validate the assumption?", "high"),
        ("did you confirm the file exists?", "high"),
        ("did you look at the actual output?", "high"),

        # Pattern 2: why is X the best/right/correct/optimal/necessary/only
        ("why is nuking the cache the best choice?", "high"),
        ("why is this approach the right one?", "high"),
        ("why are you using this method?", "none"),  # No "best/right/correct" keyword
        ("why was the previous solution optimal?", "high"),
        ("why is this the only way?", "high"),
        ("why is that necessary?", "high"),

        # Pattern 3: is this/that/it really the best/right/correct/only way/choice/approach/option
        ("is this really the best way?", "high"),
        ("is that actually the right choice?", "high"),
        ("is it truly the only option?", "high"),
        # Note: "are you sure" is LOW_STAKES by design, not HIGH

        # Pattern 4: what makes this/that/it the best/right/correct
        ("what makes this the best approach?", "high"),
        ("what makes that the right choice?", "high"),
        ("what makes it correct?", "high"),

        # Pattern 5: how do you know that/this/it
        ("how do you know that works?", "high"),
        ("how do you know this is true?", "high"),
        ("how do you know it's safe?", "high"),
    ])
    def test_investigative_challenges_classified_as_high(self, challenge: str, expected: str) -> None:
        """Investigative challenges should be classified as HIGH stakes."""
        result = _classify_prompt(challenge)
        assert result == expected, f"Challenge {challenge!r} should be {expected}, got {result}"

    def test_rca_missed_cases_now_detected(self) -> None:
        """Verify specific RCA transcript cases that were missed are now caught."""
        # Case 1: "did you sync the right way?" from transcript
        challenge1 = "did you sync the right way?"
        assert _classify_prompt(challenge1) == "high", f"Should detect: {challenge1!r}"

        # Case 2: "why is nuking the cache the best choice?" from transcript
        challenge2 = "why is nuking the cache the best choice?"
        assert _classify_prompt(challenge2) == "high", f"Should detect: {challenge2!r}"

        # Additional similar patterns
        challenge3 = "did you actually run the test?"
        assert _classify_prompt(challenge3) == "high"

        challenge4 = "what makes this the best approach?"
        assert _classify_prompt(challenge4) == "high"

    def test_low_stakes_not_affected(self) -> None:
        """LOW_STAKES_PATTERNS should remain unchanged and functional."""
        # Existing low stakes patterns should still work
        low_stakes = [
            "are you sure?",
            "is that necessary?",
            "seems overly complex",
            "i don't think that's right",
        ]

        for prompt in low_stakes:
            result = _classify_prompt(prompt)
            assert result == "low", f"Low-stakes prompt {prompt!r} should be 'low', got {result}"


# ---------------------------------------------------------------------------
# Layer 2: Widened Capitulation Pattern Tests
# ---------------------------------------------------------------------------

class TestLayer2WidenedCapitulationPatterns:
    """Layer 2: Verify widened capitulation patterns detect more variants."""

    def test_youre_right_variants_exist(self) -> None:
        """Verify new 'You're right' variants are in SYCOPHANCY_CAPITULATION_PHRASES."""
        # Pattern with optional intensifiers
        pattern1 = r"\bYou(?:'re|\s+are)\s+(?:absolutely\s+|completely\s+|totally\s+)?right\b"
        assert pattern1 in SYCOPHANCY_CAPITULATION_PHRASES

        # Pattern with continuation
        pattern2 = r"\bYou(?:'re|\s+are)\s+right\s+to\s+\w+"
        assert pattern2 in SYCOPHANCY_CAPITULATION_PHRASES

    @pytest.mark.parametrize("phrase,should_match", [
        # Should match (widened patterns)
        ("You're right", True),
        ("You are right", True),
        ("You're absolutely right", True),
        ("You're completely right", True),
        ("You're totally right", True),
        ("You're right to question that", True),
        ("You are right to be skeptical", True),

        # Should NOT match (no "right" keyword)
        ("You're correct", False),
        ("You're absolutely correct", False),
        ("You agree with me", False),

        # Should still match existing patterns
        ("I see now", True),
        ("Ah, I see", True),
        ("Now I understand", True),
        ("I was wrong about", True),
    ])
    def test_youre_right_variants_match(self, phrase: str, should_match: bool) -> None:
        """Test that widened 'You're right' patterns match correctly."""
        patterns = [re.compile(p, re.IGNORECASE) for p in SYCOPHANCY_CAPITULATION_PHRASES]
        matches = any(p.search(phrase) for p in patterns)

        if should_match:
            assert matches, f"Phrase {phrase!r} should match a capitulation pattern"
        else:
            assert not matches, f"Phrase {phrase!r} should NOT match a capitulation pattern"

    def test_punctuation_requirement_removed(self) -> None:
        """Verify that punctuation after 'right' is no longer required."""
        # Old pattern: r"You(?:'re|\s+are)\s+right[,.]" (required punctuation)
        # New pattern: r"\bYou(?:'re|\s+are)\s+(?:absolutely\s+|completely\s+|totally\s+)?right\b" (no punctuation)

        patterns = [re.compile(p, re.IGNORECASE) for p in SYCOPHANCY_CAPITULATION_PHRASES]

        # Should match without punctuation
        test_cases = [
            "You're right",
            "You are right",
            "You're absolutely right",
            "You're completely right",
        ]

        for phrase in test_cases:
            assert any(p.search(phrase) for p in patterns), f"Should match without punctuation: {phrase!r}"

    def test_rca_missed_capitulation_now_detected(self) -> None:
        """Verify specific RCA capitulation cases are now caught."""
        patterns = [re.compile(p, re.IGNORECASE) for p in SYCOPHANCY_CAPITULATION_PHRASES]

        # Case: "You're right to question that" (was missed before)
        phrase = "You're right to question that"
        assert any(p.search(phrase) for p in patterns), f"Should detect: {phrase!r}"

        # Case: "You're right" without punctuation
        phrase2 = "You're right that the cache needs clearing"
        assert any(p.search(phrase2) for p in patterns), f"Should detect: {phrase2!r}"

        # Case: "You're absolutely right"
        phrase3 = "You're absolutely right about the behavior"
        assert any(p.search(phrase3) for p in patterns), f"Should detect: {phrase3!r}"


# ---------------------------------------------------------------------------
# Layer 3: Quoted Content Exemption Tests
# ---------------------------------------------------------------------------

class TestLayer3QuotedContentExemption:
    """Layer 3: Verify quoted-content exemption prevents false positives."""

    def test_function_exists(self) -> None:
        """Verify _is_inside_quoted_content function exists."""
        assert callable(_is_inside_quoted_content), "_is_inside_quoted_content must be callable"

    @pytest.mark.parametrize("text,search_term,expected", [
        # Code block exemption
        ("```\nYou're right\n```", "You're right", True),  # Match inside code block
        ("some text ```\nYou're right\n``` more", "You're right", True),

        # Blockquote exemption
        ("> You're right about that", "You're right", True),
        ("| You are correct", "You are", True),
        ("|You're right", "You're right", True),

        # Table exemption
        ("| Column | You're right |", "You're right", True),

        # Plain text (not exempt)
        ("I agree. You're right about that.", "You're right", False),

        # Mixed code and plain text
        ("```code```\nYou're right here", "You're right", False),  # Outside code block
        ("You're right in ```code block```", "You're right", False),  # Outside code block
    ])
    def test_quoted_content_detection(self, text: str, search_term: str, expected: bool) -> None:
        """Test _is_inside_quoted_content correctly identifies quoted content."""
        # Use actual regex match
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        match = pattern.search(text)
        assert match is not None, f"Search term {search_term!r} not found in text"

        result = _is_inside_quoted_content(text, match)
        assert result == expected, f"For text {text!r} searching {search_term!r}, expected {expected}, got {result}"

    def test_code_block_fence_detection(self) -> None:
        """Test that fenced code blocks (```) are properly detected."""
        # Single code block
        text1 = """Here's my analysis:

```
User: You're right about that
Model: I see now
```

Based on the transcript..."""

        # Match inside code block should be exempt
        # Find "You're right" position (approximately)
        import re
        pattern = re.compile(r"You're right", re.IGNORECASE)
        match = pattern.search(text1)
        assert match is not None
        assert _is_inside_quoted_content(text1, match), "Match inside ``` block should be exempt"

        # Match outside code block should NOT be exempt
        pattern2 = re.compile(r"Based on", re.IGNORECASE)
        match2 = pattern2.search(text1)
        assert match2 is not None
        assert not _is_inside_quoted_content(text1, match2), "Match outside ``` block should NOT be exempt"

    def test_blockquote_detection(self) -> None:
        """Test that blockquotes (>) are properly detected."""
        text = """> User said: You're right
> Model agreed

My analysis shows..."""

        pattern = re.compile(r"You're right", re.IGNORECASE)
        match = pattern.search(text)
        assert match is not None
        assert _is_inside_quoted_content(text, match), "Match in blockquote should be exempt"

    def test_table_detection(self) -> None:
        """Test that table rows (|) are properly detected."""
        text = """| Speaker | Content |
| --- | --- |
| User | You're right |
| Model | I agree |"""

        pattern = re.compile(r"You're right", re.IGNORECASE)
        match = pattern.search(text)
        assert match is not None
        assert _is_inside_quoted_content(text, match), "Match in table should be exempt"

    def test_plain_text_not_exempt(self) -> None:
        """Test that plain text capitulation is still detected."""
        text = """After reviewing the evidence, I agree: You're right about this.
The behavior you described is correct."""

        pattern = re.compile(r"You're right", re.IGNORECASE)
        match = pattern.search(text)
        assert match is not None
        assert not _is_inside_quoted_content(text, match), "Plain text match should NOT be exempt"

    def test_nested_fence_handling(self) -> None:
        """Test that nested/odd fence counts are handled correctly."""
        # Odd number of ``` before match = inside code block
        text1 = "``` ``` ``` You're right"
        match1 = re.search(r"You're right", text1)
        assert match1 is not None
        assert _is_inside_quoted_content(text1, match1), "Odd fence count = inside block"

        # Even number of ``` before match = outside code block
        text2 = "``` ``` ``` ``` You're right"
        match2 = re.search(r"You're right", text2)
        assert match2 is not None
        assert not _is_inside_quoted_content(text2, match2), "Even fence count = outside block"


# ---------------------------------------------------------------------------
# Integration Tests: End-to-End Scenarios
# ---------------------------------------------------------------------------

class TestThreeLayerIntegration:
    """Integration tests verifying all three layers work together."""

    def test_rca_transcript_scenario(self) -> None:
        """Simulate the full RCA scenario with all three layers."""
        # User issues investigative challenge
        user_challenge = "did you sync the right way?"

        # Layer 1: Should be classified as HIGH stakes
        classification = _classify_prompt(user_challenge)
        assert classification == "high", "Challenge should trigger advocate protocol injection"

        # Model responds with capitulation (without Bash evidence)
        model_response = "You're right. The sync was incorrect."

        # Layer 2: Should detect widened capitulation pattern
        capitulation_match = any(
            re.compile(p, re.IGNORECASE).search(model_response)
            for p in SYCOPHANCY_CAPITULATION_PHRASES
        )
        assert capitulation_match, "Response should match widened capitulation pattern"

        # Layer 3: Verify exemption doesn't apply (not in quoted content)
        match = re.search(r"You're right", model_response)
        assert match is not None
        assert not _is_inside_quoted_content(model_response, match), "Plain text should not be exempt"

    def test_transcript_citation_exemption(self) -> None:
        """Verify transcript citations in code blocks are exempt."""
        # Model cites transcript evidence in code block
        response = """Looking at the transcript:

```
User: did you sync the right way?
Model: You're right, it was wrong
```

The evidence shows..."""

        # Find "You're right" match
        match = re.search(r"You're right", response)
        assert match is not None

        # Layer 3: Should be exempt (inside code block)
        assert _is_inside_quoted_content(response, match), "Code block citation should be exempt"

    def test_mixed_content_scenario(self) -> None:
        """Test mixed code block and plain text scenario."""
        response = """Here's the transcript evidence:

```python
user = "You're right about the bug"
```

However, I still think: You're correct that this needs fixing."""

        # First match in code block - should be exempt
        match1 = re.search(r"You're right", response)
        assert match1 is not None
        assert _is_inside_quoted_content(response, match1), "First match in code block should be exempt"

        # Second match in plain text - should NOT be exempt
        # (Note: "You're correct" doesn't match "You're right" pattern, but if it did...)
        match2 = re.search(r"You're correct", response)
        if match2:
            assert not _is_inside_quoted_content(response, match2), "Plain text match should NOT be exempt"


# ---------------------------------------------------------------------------
# Regression Tests: Ensure Existing Behavior Preserved
# ---------------------------------------------------------------------------

class TestRegressionExistingBehavior:
    """Verify existing behavior is not broken by the three-layer fix."""

    def test_existing_high_stakes_patterns_still_work(self) -> None:
        """Original HIGH_STAKES_PATTERNS should still work."""
        existing_high = [
            "is that really the best approach?",
            "shouldn't we just verify first?",
            "you overcomplicated this",
            "that's way too complex",
            "i just told you it was wrong",
            "did you just remove my changes?",
        ]

        for prompt in existing_high:
            result = _classify_prompt(prompt)
            assert result == "high", f"Existing high-stakes pattern should still work: {prompt!r}"

    def test_existing_low_stakes_patterns_still_work(self) -> None:
        """Original LOW_STAKES_PATTERNS should still work."""
        existing_low = [
            "are you sure?",
            "is that necessary?",
            "seems overly complex",
            "i don't think that's right",
        ]

        for prompt in existing_low:
            result = _classify_prompt(prompt)
            assert result == "low", f"Existing low-stakes pattern should still work: {prompt!r}"

    def test_existing_capitulation_patterns_still_work(self) -> None:
        """Original SYCOPHANCY_CAPITULATION_PHRASES should still work."""
        existing_capitulation = [
            "I see now",
            "Ah, I see",
            "Now I understand",
            "I was wrong about",
            "That makes sense. The fix is...",
            "So the command simply",
        ]

        patterns = [re.compile(p, re.IGNORECASE) for p in SYCOPHANCY_CAPITULATION_PHRASES]

        for phrase in existing_capitulation:
            assert any(p.search(phrase) for p in patterns), f"Existing pattern should still work: {phrase!r}"

    def test_non_challenges_classified_as_none(self) -> None:
        """Non-challenging prompts should return 'none'."""
        non_challenges = [
            "please help me with this code",
            "how do I implement X?",
            "what's the weather like?",
            "write a function to do Y",
            "explain this concept",
        ]

        for prompt in non_challenges:
            result = _classify_prompt(prompt)
            assert result == "none", f"Non-challenge should return 'none': {prompt!r}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
