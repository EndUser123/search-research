"""Tests for SEC-002: Input validation to prevent SQL injection and DoS in metrics_tracker.py.

These tests verify that the problem_hash function properly validates input
length to prevent potential SQL injection and denial-of-service attacks.
"""

import pytest

from rca.metrics_tracker import problem_hash


class TestProblemHashInputValidation:
    """Tests for input length validation in problem_hash function."""

    def test_short_input_generates_hash(self):
        """Test that short inputs generate valid hashes."""
        result = problem_hash("test error", "context")
        assert isinstance(result, str)
        assert len(result) == 16  # SHA256 truncated to 16 chars

    def test_normal_input_generates_hash(self):
        """Test that normal-sized inputs generate valid hashes."""
        problem = "ValueError: invalid literal for int() with base 10"
        context = {"file": "test.py", "line": 42}
        result = problem_hash(problem, context)
        assert isinstance(result, str)
        assert len(result) == 16

    def test_deterministic_hash_for_same_input(self):
        """Test that the same input produces the same hash."""
        problem = "test error"
        context = "test context"
        hash1 = problem_hash(problem, context)
        hash2 = problem_hash(problem, context)
        assert hash1 == hash2

    def test_case_insensitive_design(self):
        """Test that hash is case-insensitive by design (uses .lower())."""
        hash1 = problem_hash("error", "context")
        hash2 = problem_hash("Error", "context")
        # Function converts to lowercase, so these should be equal
        assert hash1 == hash2


class TestProblemHashDoSPrevention:
    """Tests for preventing denial-of-service via excessive input length."""

    def test_input_at_max_length_boundary(self):
        """Test that input exactly at MAX_INPUT_LENGTH is handled."""
        # The implementation should have MAX_INPUT_LENGTH = 10_000
        # We test the boundary behavior
        max_input = "a" * 9_990  # Under typical limit
        result = problem_hash(max_input)
        # Should still process (or handle gracefully)
        assert isinstance(result, str) or result is None

    def test_excessive_input_length_raises_error(self):
        """Test that excessively long inputs raise ValueError."""
        # Create input that exceeds MAX_INPUT_LENGTH
        # The requirement is MAX_INPUT_LENGTH = 10_000
        excessive_input = "a" * 10_001  # Just over the limit

        # The function should raise ValueError for inputs exceeding MAX_INPUT_LENGTH
        with pytest.raises(ValueError, match="Input exceeds maximum length"):
            problem_hash(excessive_input)

    def test_exactly_max_length_allowed(self):
        """Test that input exactly at MAX_INPUT_LENGTH is allowed."""
        from rca.metrics_tracker import MAX_INPUT_LENGTH

        # Input at exactly the boundary should be allowed
        max_input = "a" * MAX_INPUT_LENGTH
        result = problem_hash(max_input)
        assert isinstance(result, str)
        assert len(result) == 16

    def test_million_char_input_raises_error(self):
        """Test that extremely long input (1M chars) raises error immediately."""
        massive_input = "x" * 1_000_000  # 1 million characters

        # Should raise ValueError immediately, not process
        with pytest.raises(ValueError, match="Input exceeds maximum length"):
            problem_hash(massive_input)


class TestProblemHashSqlInjectionPrevention:
    """Tests for SQL injection prevention in problem_hash function.

    Note: problem_hash uses hashlib which is not directly vulnerable to SQLi,
    but we verify it produces safe output that could be used in SQL queries.
    """

    def test_sql_injection_attempt_in_problem(self):
        """Test that SQL injection strings produce safe hash output."""
        sql_injection = "'; DROP TABLE users; --"
        result = problem_hash(sql_injection)

        # Result should be safe hex characters only
        assert isinstance(result, str)
        assert all(c in "0123456789abcdef" for c in result)
        # Should not contain any SQL special characters
        assert "'" not in result
        assert ";" not in result
        assert "-" not in result

    def test_sql_injection_attempt_in_context(self):
        """Test that SQL injection in context produces safe hash output."""
        context = {"file": "'; DROP TABLE users; --", "line": "1 OR 1=1"}
        result = problem_hash("test", context)

        # Result should be safe hex characters only
        assert isinstance(result, str)
        assert all(c in "0123456789abcdef" for c in result)

    def test_unicode_and_special_characters(self):
        """Test that Unicode and special chars are handled safely."""
        special_inputs = [
            "Error with emoji: \U0001F600",
            "Error with null: \x00 byte",
            "Error with newlines: \n\r\t",
            "Error with quotes: ' \" `",
            "Error with unicode: \u4e2d\u6587",  # Chinese characters
        ]

        for inp in special_inputs:
            result = problem_hash(inp)
            # Should always produce safe hex output
            assert isinstance(result, str)
            assert len(result) == 16
            assert all(c in "0123456789abcdef" for c in result)


class TestProblemHashContextHandling:
    """Tests for context parameter handling."""

    def test_dict_context_produces_consistent_hash(self):
        """Test that dict contexts are serialized consistently."""
        context = {"file": "test.py", "line": 42, "error": "value"}
        result = problem_hash("error", context)

        # Same dict should produce same hash
        result2 = problem_hash("error", context)
        assert result == result2

    def test_dict_order_independence(self):
        """Test that dict key order doesn't affect hash (sort_keys=True)."""
        context1 = {"a": 1, "b": 2, "c": 3}
        context2 = {"c": 3, "a": 1, "b": 2}

        result1 = problem_hash("error", context1)
        result2 = problem_hash("error", context2)

        assert result1 == result2

    def test_string_context(self):
        """Test that string context works correctly."""
        result = problem_hash("error", "simple context string")
        assert isinstance(result, str)
        assert len(result) == 16

    def test_empty_context(self):
        """Test that empty context is handled."""
        result = problem_hash("error", "")
        assert isinstance(result, str)
        assert len(result) == 16

    def test_none_context(self):
        """Test that None context is handled."""
        result = problem_hash("error", None)
        assert isinstance(result, str)
        assert len(result) == 16


class TestProblemHashOutputSafety:
    """Tests for ensuring hash output is safe for all use cases."""

    def test_hash_is_hex_string(self):
        """Test that hash output is pure hexadecimal."""
        result = problem_hash("any input", {"any": "context"})
        assert isinstance(result, str)
        # Should be lowercase hex
        assert result.islower() or all(c in "0123456789abcdef" for c in result)

    def test_hash_length_consistency(self):
        """Test that hash length is always consistent."""
        results = [
            problem_hash(str(i), {"context": i})
            for i in range(100)
        ]

        # All should have same length
        lengths = {len(r) for r in results}
        assert lengths == {16}

    def test_hash_distribution(self):
        """Test that different inputs produce different hashes."""
        results = set()
        for i in range(100):
            h = problem_hash(f"error_{i}", {"id": i})
            results.add(h)

        # Should have good distribution (at least 95% unique)
        assert len(results) >= 95


class TestProblemHashIntegration:
    """Integration tests for problem_hash with metrics tracker."""

    def test_hash_can_be_used_in_sql_query(self):
        """Test that hash output is safe to use as SQL parameter."""
        # This is a documentation test - hashes should ALWAYS be
        # used as parameters, not interpolated into SQL
        problem = "'; DROP TABLE rca_sessions; --"
        context = {"file": "../../etc/passwd"}

        result = problem_hash(problem, context)

        # Verify safe characters for SQL parameter binding
        assert isinstance(result, str)
        assert len(result) == 16
        # Pure hex is always safe for SQL parameters
        assert all(c in "0123456789abcdef" for c in result)

    def test_real_world_error_messages(self):
        """Test that real-world error messages produce valid hashes."""
        real_errors = [
            "ImportError: No module named 'requests'",
            "FileNotFoundError: [Errno 2] No such file or directory: 'config.json'",
            "ConnectionError: HTTPConnectionPool(host='api.example.com', port=443): "
            "Max retries exceeded with url: /api/v1/endpoint",
            "json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)",
            "AssertionError: Expected 200 but got 500",
        ]

        for error in real_errors:
            result = problem_hash(error)
            assert isinstance(result, str)
            assert len(result) == 16
