"""Tests for hypothesis_generator module.

NOTE: Creating new test file for hypothesis_generator module which currently has no test coverage.
"""

import pytest

from rca.hypothesis_generator import (
    HypothesisCategory,
    Hypothesis,
    HypothesisSet,
    generate_hypotheses,
    DEFAULT_WEIGHTS,
)


class TestHypothesisCategory:
    """Tests for HypothesisCategory enum."""

    def test_category_values(self):
        """Test that category values are strings."""
        assert HypothesisCategory.OFF_BY_ONE.value == "off_by_one"
        assert HypothesisCategory.NULL_DEREFERENCE.value == "null_dereference"
        assert HypothesisCategory.TYPE_MISMATCH.value == "type_mismatch"

    def test_all_categories_exist(self):
        """Test that expected categories exist."""
        expected_categories = [
            "off_by_one",
            "null_dereference",
            "type_mismatch",
            "missing_guard",
            "wrong_operator",
            "incorrect_return",
            "state_corruption",
            "race_condition",
            "resource_leak",
            "config_error",
            "dependency_version",
            "encoding_error",
        ]
        for cat in expected_categories:
            assert hasattr(HypothesisCategory, cat.upper())


class TestHypothesis:
    """Tests for Hypothesis dataclass."""

    def test_hypothesis_creation(self):
        """Test creating a Hypothesis."""
        hyp = Hypothesis(
            category=HypothesisCategory.NULL_DEREFERENCE,
            description="Object is None",
            target_location="main.py",
            priority_weight=1.0,
            falsification_test="Add logging",
        )
        assert hyp.category == HypothesisCategory.NULL_DEREFERENCE
        assert hyp.description == "Object is None"
        assert hyp.target_location == "main.py"
        assert hyp.priority_weight == 1.0
        assert hyp.falsification_test == "Add logging"

    def test_hypothesis_default_values(self):
        """Test default values for optional fields."""
        hyp = Hypothesis(
            category=HypothesisCategory.TYPE_MISMATCH,
            description="Type mismatch",
            target_location="file.py",
            priority_weight=0.8,
            falsification_test="Check type",
        )
        assert hyp.supporting_evidence == []
        assert hyp.contradicting_evidence == []
        assert hyp.status == "pending"

    def test_hypothesis_with_evidence_lists(self):
        """Test hypothesis with evidence lists."""
        hyp = Hypothesis(
            category=HypothesisCategory.OFF_BY_ONE,
            description="Index error",
            target_location="loop.py",
            priority_weight=0.9,
            falsification_test="Check bounds",
            supporting_evidence=["evidence 1", "evidence 2"],
            contradicting_evidence=["counter-evidence"],
            status="investigating",
        )
        assert len(hyp.supporting_evidence) == 2
        assert len(hyp.contradicting_evidence) == 1
        assert hyp.status == "investigating"


class TestHypothesisSet:
    """Tests for HypothesisSet dataclass."""

    def test_hypothesis_set_creation(self):
        """Test creating a HypothesisSet."""
        hyp1 = Hypothesis(
            category=HypothesisCategory.NULL_DEREFERENCE,
            description="None object",
            target_location="file.py",
            priority_weight=1.0,
            falsification_test="Log value",
        )
        hyp2 = Hypothesis(
            category=HypothesisCategory.TYPE_MISMATCH,
            description="Wrong type",
            target_location="file.py",
            priority_weight=0.8,
            falsification_test="Check type",
        )
        hypothesis_set = HypothesisSet(
            error_signature="AttributeError: None",
            hypotheses=[hyp1, hyp2],
        )
        assert hypothesis_set.error_signature == "AttributeError: None"
        assert len(hypothesis_set.hypotheses) == 2
        assert hypothesis_set.null_hypothesis is None

    def test_hypothesis_set_with_null_hypothesis(self):
        """Test HypothesisSet with null hypothesis."""
        null_hyp = Hypothesis(
            category=HypothesisCategory.CONFIG_ERROR,
            description="External error",
            target_location="external",
            priority_weight=0.3,
            falsification_test="Trace stack",
        )
        hypothesis_set = HypothesisSet(
            error_signature="Error",
            hypotheses=[],
            null_hypothesis=null_hyp,
        )
        assert hypothesis_set.null_hypothesis == null_hyp

    def test_rank_by_priority(self):
        """Test rank_by_priority method."""
        hyp1 = Hypothesis(
            category=HypothesisCategory.MISSING_GUARD,
            description="Low priority",
            target_location="file.py",
            priority_weight=0.5,
            falsification_test="Test",
        )
        hyp2 = Hypothesis(
            category=HypothesisCategory.NULL_DEREFERENCE,
            description="High priority",
            target_location="file.py",
            priority_weight=1.0,
            falsification_test="Test",
        )
        hyp3 = Hypothesis(
            category=HypothesisCategory.TYPE_MISMATCH,
            description="Medium priority",
            target_location="file.py",
            priority_weight=0.8,
            falsification_test="Test",
        )
        hypothesis_set = HypothesisSet(
            error_signature="Error",
            hypotheses=[hyp1, hyp2, hyp3],
        )
        ranked = hypothesis_set.rank_by_priority()
        assert ranked[0].priority_weight >= ranked[1].priority_weight
        assert ranked[1].priority_weight >= ranked[2].priority_weight
        assert ranked[0] == hyp2


class TestGenerateHypotheses:
    """Tests for generate_hypotheses function."""

    def test_generate_hypotheses_returns_hypothesis_set(self):
        """Test that generate_hypotheses returns a HypothesisSet."""
        result = generate_hypotheses(
            error_type="AttributeError",
            error_message="'NoneType' object has no attribute",
            target_file="main.py",
        )
        assert isinstance(result, HypothesisSet)
        assert isinstance(result.hypotheses, list)
        assert isinstance(result.null_hypothesis, Hypothesis)

    def test_generate_hypotheses_attribute_error(self):
        """Test hypothesis generation for AttributeError."""
        result = generate_hypotheses(
            error_type="AttributeError",
            error_message="'NoneType' object has no attribute 'x'",
            target_file="handler.py",
        )
        assert len(result.hypotheses) >= 2
        categories = [h.category for h in result.hypotheses]
        assert HypothesisCategory.NULL_DEREFERENCE in categories
        assert HypothesisCategory.TYPE_MISMATCH in categories

    def test_generate_hypotheses_type_error(self):
        """Test hypothesis generation for TypeError."""
        result = generate_hypotheses(
            error_type="TypeError",
            error_message="'int' object is not subscriptable",
            target_file="utils.py",
        )
        assert len(result.hypotheses) >= 2
        categories = [h.category for h in result.hypotheses]
        assert HypothesisCategory.NULL_DEREFERENCE in categories
        assert HypothesisCategory.TYPE_MISMATCH in categories

    def test_generate_hypotheses_index_error(self):
        """Test hypothesis generation for IndexError."""
        result = generate_hypotheses(
            error_type="IndexError",
            error_message="list index out of range",
            target_file="loop.py",
        )
        assert len(result.hypotheses) >= 2
        categories = [h.category for h in result.hypotheses]
        assert HypothesisCategory.OFF_BY_ONE in categories
        assert HypothesisCategory.MISSING_GUARD in categories

    def test_generate_hypotheses_key_error(self):
        """Test hypothesis generation for KeyError."""
        result = generate_hypotheses(
            error_type="KeyError",
            error_message="'config'",
            target_file="config.py",
        )
        assert len(result.hypotheses) >= 1
        assert any(h.category == HypothesisCategory.MISSING_GUARD for h in result.hypotheses)

    def test_generate_hypotheses_module_not_found(self):
        """Test hypothesis generation for ModuleNotFoundError."""
        result = generate_hypotheses(
            error_type="ModuleNotFoundError",
            error_message="No module named 'requests'",
            target_file="main.py",
        )
        assert any(h.category == HypothesisCategory.DEPENDENCY_VERSION for h in result.hypotheses)

    def test_generate_hypotheses_import_in_message(self):
        """Test hypothesis generation when 'import' is in error message."""
        result = generate_hypotheses(
            error_type="AttributeError",
            error_message="Failed to import module",
            target_file="main.py",
        )
        assert any(h.category == HypothesisCategory.DEPENDENCY_VERSION for h in result.hypotheses)

    def test_generate_hypotheses_value_error(self):
        """Test hypothesis generation for ValueError."""
        result = generate_hypotheses(
            error_type="ValueError",
            error_message="invalid literal for int()",
            target_file="parser.py",
        )
        assert len(result.hypotheses) >= 2
        categories = [h.category for h in result.hypotheses]
        assert HypothesisCategory.TYPE_MISMATCH in categories
        assert HypothesisCategory.MISSING_GUARD in categories

    def test_generate_hypotheses_file_not_found(self):
        """Test hypothesis generation for FileNotFoundError."""
        result = generate_hypotheses(
            error_type="FileNotFoundError",
            error_message="No such file or directory",
            target_file="io.py",
        )
        assert any(h.category == HypothesisCategory.CONFIG_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_permission_error(self):
        """Test hypothesis generation for PermissionError."""
        result = generate_hypotheses(
            error_type="PermissionError",
            error_message="Permission denied",
            target_file="file.py",
        )
        assert any(h.category == HypothesisCategory.CONFIG_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_timeout_error(self):
        """Test hypothesis generation for TimeoutError."""
        result = generate_hypotheses(
            error_type="TimeoutError",
            error_message="Operation timed out",
            target_file="network.py",
        )
        assert any(h.category == HypothesisCategory.RACE_CONDITION for h in result.hypotheses)

    def test_generate_hypotheses_timeout_in_message(self):
        """Test hypothesis generation when 'timeout' is in error message."""
        result = generate_hypotheses(
            error_type="RuntimeError",
            error_message="Request timeout after 30 seconds",
            target_file="api.py",
        )
        assert any(h.category == HypothesisCategory.RACE_CONDITION for h in result.hypotheses)

    def test_generate_hypotheses_connection_error(self):
        """Test hypothesis generation for ConnectionError."""
        result = generate_hypotheses(
            error_type="ConnectionError",
            error_message="Connection refused",
            target_file="client.py",
        )
        assert any(h.category == HypothesisCategory.CONFIG_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_connection_in_message(self):
        """Test hypothesis generation when 'connection' is in error message."""
        result = generate_hypotheses(
            error_type="RuntimeError",
            error_message="Failed to establish connection",
            target_file="network.py",
        )
        assert any(h.category == HypothesisCategory.CONFIG_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_unicode_decode_error(self):
        """Test hypothesis generation for UnicodeDecodeError."""
        result = generate_hypotheses(
            error_type="UnicodeDecodeError",
            error_message="'utf-8' codec can't decode byte",
            target_file="reader.py",
        )
        assert any(h.category == HypothesisCategory.ENCODING_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_unicode_encode_error(self):
        """Test hypothesis generation for UnicodeEncodeError."""
        result = generate_hypotheses(
            error_type="UnicodeEncodeError",
            error_message="'ascii' codec can't encode",
            target_file="writer.py",
        )
        assert any(h.category == HypothesisCategory.ENCODING_ERROR for h in result.hypotheses)

    def test_generate_hypotheses_recursion_error(self):
        """Test hypothesis generation for RecursionError."""
        result = generate_hypotheses(
            error_type="RecursionError",
            error_message="maximum recursion depth exceeded",
            target_file="recursive.py",
        )
        assert any(h.category == HypothesisCategory.STATE_CORRUPTION for h in result.hypotheses)

    def test_generate_hypotheses_recursion_in_message(self):
        """Test hypothesis generation when 'recursion' is in error message."""
        result = generate_hypotheses(
            error_type="RuntimeError",
            error_message="Detected recursion in call stack",
            target_file="tree.py",
        )
        assert any(h.category == HypothesisCategory.STATE_CORRUPTION for h in result.hypotheses)

    def test_generate_hypotheses_assertion_error(self):
        """Test hypothesis generation for AssertionError."""
        result = generate_hypotheses(
            error_type="AssertionError",
            error_message="Assertion failed",
            target_file="check.py",
        )
        assert any(h.category == HypothesisCategory.STATE_CORRUPTION for h in result.hypotheses)

    def test_generate_hypotheses_zero_division_error(self):
        """Test hypothesis generation for ZeroDivisionError."""
        result = generate_hypotheses(
            error_type="ZeroDivisionError",
            error_message="division by zero",
            target_file="math.py",
        )
        assert any(h.category == HypothesisCategory.MISSING_GUARD for h in result.hypotheses)

    def test_generate_hypotheses_memory_error(self):
        """Test hypothesis generation for MemoryError."""
        result = generate_hypotheses(
            error_type="MemoryError",
            error_message="out of memory",
            target_file="processor.py",
        )
        assert any(h.category == HypothesisCategory.RESOURCE_LEAK for h in result.hypotheses)

    def test_generate_hypotheses_null_hypothesis(self):
        """Test that null hypothesis is always generated."""
        result = generate_hypotheses(
            error_type="AttributeError",
            error_message="error",
            target_file="file.py",
        )
        assert result.null_hypothesis is not None
        assert result.null_hypothesis.target_location == "external"
        assert result.null_hypothesis.priority_weight == 0.3

    def test_generate_hypotheses_with_custom_weights(self):
        """Test generate_hypotheses with custom weights."""
        custom_weights = {
            "null_dereference": 0.5,
            "type_mismatch": 0.9,
            "off_by_one": 1.0,
        }
        result = generate_hypotheses(
            error_type="AttributeError",
            error_message="error",
            target_file="file.py",
            weights=custom_weights,
        )
        for hyp in result.hypotheses:
            category_key = hyp.category.value
            if category_key in custom_weights:
                assert hyp.priority_weight == custom_weights[category_key]

    def test_generate_hypotheses_unknown_error_type(self):
        """Test generate_hypotheses with unknown error type."""
        result = generate_hypotheses(
            error_type="CustomError",
            error_message="something unexpected",
            target_file="file.py",
        )
        # Should still return a HypothesisSet with null hypothesis
        assert isinstance(result, HypothesisSet)
        assert result.null_hypothesis is not None

    def test_generate_hypotheses_error_signature_truncation(self):
        """Test that error_signature is truncated to 100 chars."""
        long_message = "x" * 200
        result = generate_hypotheses(
            error_type="Error",
            error_message=long_message,
            target_file="file.py",
        )
        assert len(result.error_signature) <= 100 + len("Error: ")


class TestDefaultWeights:
    """Tests for DEFAULT_WEIGHTS constant."""

    def test_all_weights_are_positive(self):
        """Test that all default weights are positive."""
        for key, weight in DEFAULT_WEIGHTS.items():
            assert weight > 0, f"Weight for {key} is not positive: {weight}"

    def test_all_weights_are_float(self):
        """Test that all weights are floats."""
        for key, weight in DEFAULT_WEIGHTS.items():
            assert isinstance(weight, float)

    def test_expected_weights_exist(self):
        """Test that expected weight keys exist."""
        expected_keys = [
            "null_dereference",
            "type_mismatch",
            "off_by_one",
            "missing_guard",
            "dependency_version",
            "config_error",
            "race_condition",
            "encoding_error",
            "state_corruption",
            "resource_leak",
        ]
        for key in expected_keys:
            assert key in DEFAULT_WEIGHTS
