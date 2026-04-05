"""
Tests for unverified_stance_detector.py

Test coverage for existing unverified_stance_detector module.
"""

import pytest
from anti_sycophancy.unverified_stance_detector import (
    detect_unverified_stance,
)


class TestUnverifiedStanceDetector:
    """Test suite for unverified stance detection."""

    def test_sycophantic_doubt_opencclaw_case(self):
        """Test the real-world OpenClaw failure case."""
        data = {
            "response": "You're right to push back on that. Let me verify OpenClaw's actual adoption.",
            "transcript": [{"role": "user", "content": "I heard that OpenClaw is used by millions of solo people."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None
        assert result.category == "sycophantic_doubt"

    def test_empty_hedge_that_sounds_high(self):
        """Test empty hedge with 'that sounds high' pattern."""
        data = {
            "response": "That sounds high, let me verify that number.",
            "transcript": [{"role": "user", "content": "PyTorch has over 100k stars on GitHub."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None
        assert result.category == "empty_hedge"

    def test_hedge_with_websearch_verification(self):
        """Hedge followed by actual WebSearch verification - should allow."""
        data = {
            "response": "Let me verify that number.",
            "transcript": [{"role": "user", "content": "React has 200k stars."}],
            "tools_used": [{"name": "WebSearch"}],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is None

    def test_user_asks_question_not_claim(self):
        """User asking a question, not stating a fact - should allow."""
        data = {
            "response": "Let me check on that for you.",
            "transcript": [{"role": "user", "content": "How many stars does React have?"}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is None

    def test_self_prompt_contains_guidance(self):
        """Self-prompt should contain expected guidance."""
        data = {
            "response": "You're right to push back on that.",
            "transcript": [{"role": "user", "content": "OpenClaw has millions of users."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None
        assert "UNVERIFIED STANCE CHECK" in result.self_prompt

    def test_doubt_without_checking(self):
        """I doubt that without checking - should detect."""
        data = {
            "response": "I doubt that's accurate. The number seems inflated.",
            "transcript": [{"role": "user", "content": "OpenClaw has 145k GitHub stars."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None, "Should detect doubt without checking"

    def test_negative_claim_with_doubt(self):
        """Negative factual claim with doubt - should detect."""
        data = {
            "response": "I doubt that's true. OpenClaw isn't that popular.",
            "transcript": [{"role": "user", "content": "OpenClaw has 145k stars."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None, "Should detect negative claim + doubt"

    def test_compound_sycophantic_phrases(self):
        """Multiple sycophantic doubt phrases - should detect."""
        data = {
            "response": "You're right to be skeptical. That sounds unlikely.",
            "transcript": [{"role": "user", "content": "I heard OpenClaw has billions of users."}],
            "tools_used": [],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is not None, "Should detect compound phrases"

    def test_bash_counts_as_verification(self):
        """Bash tool counts as verification - should allow."""
        data = {
            "response": "Let me verify those stars.",
            "transcript": [{"role": "user", "content": "React has 200k stars."}],
            "tools_used": [{"name": "Bash"}],
        }
        result = detect_unverified_stance(data["response"], data)
        assert result is None, "Should allow when Bash used"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
