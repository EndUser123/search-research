"""
Acceptance tests for cognitive enhancers intent detection.

From ADR-20260322-hook-intent-detection-revised.md acceptance criteria:
- Accuracy: >90% precision on held-out test corpus
- Coverage: Detect 30% more intents than baseline patterns
- Performance: <10ms latency per classification
- False positive rate: <5% on negative corpus
"""

# Import the intent detection function
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cognitive_enhancers import _detect_intent


class TestIntentDetectionPositiveCases:
    """Positive cases - should trigger intent detection."""

    def test_implementation_intent(self):
        """'implement a new feature' should trigger implementation."""
        prompt = "implement a new feature for user authentication"
        result = _detect_intent(prompt)
        assert result["implementation"] is True, f"Expected implementation=True, got {result}"
        assert result["diagnostic"] is False
        assert result["decomposition"] is False

    def test_diagnostic_intent(self):
        """'debug this issue' should trigger diagnostic."""
        prompt = "debug this issue with the session resume mechanism"
        result = _detect_intent(prompt)
        assert result["diagnostic"] is True, f"Expected diagnostic=True, got {result}"
        assert result["implementation"] is False
        assert result["decomposition"] is False

    def test_decomposition_intent(self):
        """'break down this task' should trigger decomposition (LOGIC-001 fix)."""
        prompt = "break down this task into smaller subtasks"
        result = _detect_intent(prompt)
        assert result["decomposition"] is True, f"Expected decomposition=True, got {result}"
        # This is a pure decomposition prompt, not implementation
        assert result["implementation"] is False

    def test_enhance_implementation_intent(self):
        """'enhance session resume' should trigger implementation (coverage gap fix)."""
        prompt = "enhance session resume mechanism to support faster handoffs"
        result = _detect_intent(prompt)
        assert result["implementation"] is True, f"Expected implementation=True, got {result}"
        assert result["diagnostic"] is False


class TestIntentDetectionNegativeCases:
    """Negative cases - should NOT trigger intent detection."""

    def test_explain_only(self):
        """'explain how authentication works' should be information only."""
        prompt = "explain how authentication works in this system"
        result = _detect_intent(prompt)
        # "explain" without "why" or diagnostic context is not diagnostic
        assert result["diagnostic"] is False
        assert result["implementation"] is False

    def test_list_command(self):
        """'list all files' should be command only."""
        prompt = "list all files in the current directory"
        result = _detect_intent(prompt)
        assert result["implementation"] is False
        assert result["diagnostic"] is False
        assert result["decomposition"] is False

    def test_off_topic(self):
        """'what's the weather' should be off-topic."""
        prompt = "what's the weather like today"
        result = _detect_intent(prompt)
        assert result["implementation"] is False
        assert result["diagnostic"] is False
        assert result["decomposition"] is False

    def test_negation(self):
        """'don't implement this' should be blocked by negation detection."""
        prompt = "don't implement this feature yet"
        result = _detect_intent(prompt)
        # Negation should block implementation intent
        assert result["implementation"] is False, "Negation should block implementation intent"


class TestIntentDetectionPerformance:
    """Performance and accuracy tests."""

    def test_classification_latency(self):
        """Classification should be <10ms per classification (ADR acceptance criterion)."""
        prompts = [
            "implement a new feature",
            "debug this issue",
            "break down this task",
            "enhance session resume",
            "explain how authentication works",
        ]

        latencies = []
        for prompt in prompts:
            start = time.perf_counter_ns()
            _detect_intent(prompt)
            end = time.perf_counter_ns()
            latency_ms = (end - start) / 1_000_000
            latencies.append(latency_ms)

        max_latency = max(latencies)
        avg_latency = sum(latencies) / len(latencies)

        print(f"\nLatency results: max={max_latency:.2f}ms, avg={avg_latency:.2f}ms")
        assert (
            max_latency < 10
        ), f"Classification latency {max_latency:.2f}ms exceeds 10ms requirement"

    def test_precision_on_test_corpus(self):
        """Test corpus precision should be >90% (ADR acceptance criterion).

        This is a baseline test - actual precision measurement requires
        a larger held-out corpus.
        """
        test_cases = [
            # (prompt, expected_implementation, expected_diagnostic, expected_decomposition)
            ("implement a new feature", True, False, False),
            ("debug this issue", False, True, False),
            ("break down this task", False, False, True),
            ("enhance session resume", True, False, False),
            ("explain how authentication works", False, False, False),
            ("list all files", False, False, False),
            ("what's the weather", False, False, False),
            ("don't implement this", False, False, False),
        ]

        correct = 0
        total = len(test_cases)

        for prompt, exp_impl, exp_diag, exp_decomp in test_cases:
            result = _detect_intent(prompt)
            if (
                result["implementation"] == exp_impl
                and result["diagnostic"] == exp_diag
                and result["decomposition"] == exp_decomp
            ):
                correct += 1

        precision = correct / total
        print(f"\nPrecision: {precision:.1%} ({correct}/{total} correct)")

        # ADR requires >90% precision - this test verifies our test corpus meets that bar
        assert precision >= 0.90, f"Precision {precision:.1%} below 90% requirement"


class TestIntentDetectionEdgeCases:
    """Edge case testing."""

    def test_mixed_intent(self):
        """Prompts with multiple trigger words should handle precedence."""
        # "implement and debug" has both implementation and diagnostic keywords
        prompt = "implement and debug the authentication system"
        result = _detect_intent(prompt)
        # Should detect implementation (first pattern match wins in current implementation)
        assert result["implementation"] is True or result["diagnostic"] is True

    def test_case_insensitive(self):
        """Intent detection should be case-insensitive."""
        prompts = [
            "IMPLEMENT A NEW FEATURE",
            "Implement a new feature",
            "implement a new feature",
        ]

        for prompt in prompts:
            result = _detect_intent(prompt)
            assert result["implementation"] is True, f"Case-insensitive failed for: {prompt}"

    def test_partial_word_matches(self):
        """Should require word boundaries, not partial matches."""
        # "implementation" contains "implement" as substring
        prompt = "the implementation is already complete"
        result = _detect_intent(prompt)
        # Current regex uses \b word boundaries, so this should NOT match
        # (the word "implementation" is not the same as "implement")
        # This tests that we're not doing substring matching
        assert (
            result["implementation"] is False
        ), "Should not match 'implement' inside 'implementation'"
