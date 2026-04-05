"""Tests for fault_localization module.

Tests for fault detection and localization algorithms.
"""

import pytest

from rca.fault_localization import (
    FaultLocalizationResult,
    FaultLocalizer,
    FaultType,
)


class TestFaultType:
    """Test FaultType enum."""

    def test_fault_type_values(self):
        """FaultType has expected values."""
        assert FaultType.LOGIC_ERROR.value == "logic_error"
        assert FaultType.NULL_POINTER.value == "null_pointer"
        assert FaultType.TYPE_ERROR.value == "type_error"
        assert FaultType.CONCURRENCY_BUG.value == "concurrency_bug"


class TestFaultLocalizationResult:
    """Test FaultLocalizationResult dataclass."""

    def test_result_creation(self):
        """FaultLocalizationResult can be created."""
        result = FaultLocalizationResult(
            fault_type=FaultType.NULL_POINTER,
            location="src/handler.py:42",
            confidence=0.85,
            context="Variable 'data' is None",
        )

        assert result.fault_type == FaultType.NULL_POINTER
        assert result.location == "src/handler.py:42"
        assert result.confidence == 0.85

    def test_result_with_suggestions(self):
        """Result can include fix suggestions."""
        result = FaultLocalizationResult(
            fault_type=FaultType.LOGIC_ERROR,
            location="src/utils.py:15",
            confidence=0.7,
            fix_suggestions=["Add null check", "Validate input"],
        )

        assert len(result.fix_suggestions) == 2


class TestFaultLocalizerInit:
    """Test FaultLocalizer initialization."""

    def test_localizer_creation(self):
        """FaultLocalizer can be created."""
        localizer = FaultLocalizer()

        assert localizer is not None


class TestLocalizeFromStackTrace:
    """Test fault localization from stack traces."""

    def test_localize_from_simple_trace(self):
        """Simple stack trace can be localized."""
        localizer = FaultLocalizer()
        stack_trace = """
Traceback (most recent call last):
  File "src/handler.py", line 42, in process_request
    data = items[0]
IndexError: list index out of range
"""

        result = localizer.localize_from_stack_trace(stack_trace)

        assert result is not None
        assert result.location is not None
        assert "handler.py" in result.location

    def test_localize_with_attribute_error(self):
        """AttributeError can be localized."""
        localizer = FaultLocalizer()
        stack_trace = """
Traceback (most recent call last):
  File "src/model.py", line 15, in validate
    if self.data.value:
AttributeError: 'NoneType' object has no attribute 'value'
"""

        result = localizer.localize_from_stack_trace(stack_trace)

        assert result is not None
        assert result.fault_type == FaultType.NULL_POINTER

    def test_localize_with_type_error(self):
        """TypeError can be localized."""
        localizer = FaultLocalizer()
        stack_trace = """
Traceback (most recent call last):
  File "src/utils.py", line 23, in calculate
    return x + y
TypeError: can only concatenate str (not "int") to str
"""

        result = localizer.localize_from_stack_trace(stack_trace)

        assert result is not None
        assert result.fault_type == FaultType.TYPE_ERROR


class TestLocalizeFromErrorPattern:
    """Test fault localization from error patterns."""

    def test_localize_from_none_access(self):
        """None access pattern is detected."""
        localizer = FaultLocalizer()
        error = "AttributeError: 'NoneType' object has no attribute 'x'"

        result = localizer.localize_from_error_pattern(error)

        assert result is not None
        assert result.fault_type == FaultType.NULL_POINTER

    def test_localize_from_key_error(self):
        """KeyError pattern is detected."""
        localizer = FaultLocalizer()
        error = "KeyError: 'missing_key'"

        result = localizer.localize_from_error_pattern(error)

        assert result is not None

    def test_localize_from_import_error(self):
        """ImportError pattern is detected."""
        localizer = FaultLocalizer()
        error = "ImportError: No module named 'missing_package'"

        result = localizer.localize_from_error_pattern(error)

        assert result is not None


class TestGetFaultType:
    """Test fault type detection."""

    def test_detect_none_pointer(self):
        """None pointer is detected."""
        localizer = FaultLocalizer()

        fault_type = localizer.get_fault_type("AttributeError: 'NoneType' object")

        assert fault_type == FaultType.NULL_POINTER

    def test_detect_type_error(self):
        """Type error is detected."""
        localizer = FaultLocalizer()

        fault_type = localizer.get_fault_type("TypeError: unsupported operand")

        assert fault_type == FaultType.TYPE_ERROR

    def test_detect_logic_error(self):
        """Logic error is detected."""
        localizer = FaultLocalizer()

        fault_type = localizer.get_fault_type("IndexError: list index out of range")

        assert fault_type == FaultType.LOGIC_ERROR


class TestGenerateFixSuggestions:
    """Test fix suggestion generation."""

    def test_suggestions_for_null_pointer(self):
        """Null pointer gets appropriate suggestions."""
        localizer = FaultLocalizer()

        result = FaultLocalizationResult(
            fault_type=FaultType.NULL_POINTER,
            location="test.py:10",
            confidence=0.8,
        )

        suggestions = localizer.generate_fix_suggestions(result)

        assert len(suggestions) > 0
        assert any("null" in s.lower() or "check" in s.lower() for s in suggestions)

    def test_suggestions_for_type_error(self):
        """Type error gets appropriate suggestions."""
        localizer = FaultLocalizer()

        result = FaultLocalizationResult(
            fault_type=FaultType.TYPE_ERROR,
            location="test.py:10",
            confidence=0.8,
        )

        suggestions = localizer.generate_fix_suggestions(result)

        assert len(suggestions) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_stack_trace(self):
        """Empty stack trace returns None."""
        localizer = FaultLocalizer()

        result = localizer.localize_from_stack_trace("")

        assert result is None

    def test_malformed_stack_trace(self):
        """Malformed stack trace is handled."""
        localizer = FaultLocalizer()

        result = localizer.localize_from_stack_trace("This is not a stack trace")

        # Should not crash
        assert result is None or isinstance(result, FaultLocalizationResult)

    def test_unknown_error_type(self):
        """Unknown error type defaults to logic error."""
        localizer = FaultLocalizer()

        fault_type = localizer.get_fault_type("UnknownError: something happened")

        assert fault_type == FaultType.LOGIC_ERROR
