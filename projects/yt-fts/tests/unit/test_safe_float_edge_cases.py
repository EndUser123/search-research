"""
Unit tests for _safe_float() edge cases.

These tests verify that _safe_float handles unusual and edge case inputs correctly,
returning a default value instead of crashing or returning invalid floats.

Run with: pytest tests/unit/test_safe_float_edge_cases.py -v
"""
import math
import pytest
from unittest.mock import MagicMock
from yt_fts.utils.types import _safe_float


class TestSafeFloatNoneValues:
    """Tests for None value handling."""

    @pytest.mark.parametrize("value", [None, "None", "null", "", ""])
    def test_returns_default_for_none_values(self, value):
        """
        Test that _safe_float returns default value for None-like inputs.

        Given: A None or None-like value
        When: Calling _safe_float with the value
        Then: Should return the provided default value
        """
        result = _safe_float(value, default=0.0)
        assert result == 0.0

    def test_returns_custom_default_for_none(self):
        """
        Test that _safe_float returns custom default value.

        Given: A None value with custom default
        When: Calling _safe_float with default=-1.0
        Then: Should return -1.0
        """
        result = _safe_float(None, default=-1.0)
        assert result == -1.0


class TestSafeFloatMagicMockHandling:
    """Tests for MagicMock object handling."""

    def test_handles_magicmock_objects(self):
        """
        Test that _safe_float handles MagicMock objects correctly.

        Given: A MagicMock object (common in testing scenarios)
        When: Calling _safe_float with the MagicMock
        Then: Should return the default value instead of crashing
        """
        mock_obj = MagicMock()
        result = _safe_float(mock_obj, default=0.0)
        assert result == 0.0

    def test_handles_magicmock_with_float_attribute(self):
        """
        Test that _safe_float doesn't get confused by MagicMock attributes.

        Given: A MagicMock that might have __float__ behavior
        When: Calling _safe_float with the mock
        Then: Should return the default value safely
        """
        mock_obj = MagicMock()
        mock_obj.__float__ = MagicMock(return_value=42.0)
        result = _safe_float(mock_obj, default=0.0)
        # Should return default, not the mock's float conversion
        assert result == 0.0


class TestSafeFloatSpecialFloatValues:
    """Tests for special float values (infinity, NaN)."""

    @pytest.mark.parametrize("value", [
        float('inf'),
        float('-inf'),
        math.inf,
        -math.inf,
    ])
    def test_returns_default_for_infinity_values(self, value):
        """
        Test that _safe_float returns default for infinity values.

        Given: An infinity value (positive or negative)
        When: Calling _safe_float with the infinity value
        Then: Should return the default value
        """
        result = _safe_float(value, default=0.0)
        assert result == 0.0

    @pytest.mark.parametrize("value", [
        float('nan'),
        math.nan,
    ])
    def test_returns_default_for_nan_values(self, value):
        """
        Test that _safe_float returns default for NaN values.

        Given: A NaN (Not a Number) value
        When: Calling _safe_float with the NaN value
        Then: Should return the default value
        """
        result = _safe_float(value, default=0.0)
        assert result == 0.0


class TestSafeFloatComplexNumbers:
    """Tests for complex number handling."""

    @pytest.mark.parametrize("value", [
        complex(1, 2),
        complex(0, 1),
        complex(3.14, -2.71),
        1j,
        3+4j,
    ])
    def test_returns_default_for_complex_numbers(self, value):
        """
        Test that _safe_float returns default for complex numbers.

        Given: A complex number (e.g., 3+4j)
        When: Calling _safe_float with the complex number
        Then: Should return the default value instead of raising TypeError
        """
        result = _safe_float(value, default=0.0)
        assert result == 0.0


class TestSafeFloatValidConversions:
    """Tests for valid float conversions (baseline)."""

    @pytest.mark.parametrize("value,expected", [
        (42, 42.0),
        (3.14, 3.14),
        ("42", 42.0),
        ("3.14", 3.14),
        (0, 0.0),
        (-1.5, -1.5),
        ("-10", -10.0),
    ])
    def test_converts_valid_inputs_to_float(self, value, expected):
        """
        Test that _safe_float converts valid inputs correctly.

        Given: A valid numeric input
        When: Calling _safe_float with the input
        Then: Should return the correctly converted float value
        """
        result = _safe_float(value, default=0.0)
        assert result == expected


class TestSafeFloatInvalidTypes:
    """Tests for other invalid types."""

    @pytest.mark.parametrize("value", [
        [1, 2, 3],
        {"key": "value"},
        {"set", "of", "items"},
        lambda x: x,
        bytearray(b"test"),
    ])
    def test_returns_default_for_invalid_types(self, value):
        """
        Test that _safe_float returns default for unconvertible types.

        Given: An invalid type (list, dict, set, function, etc.)
        When: Calling _safe_float with the invalid type
        Then: Should return the default value instead of raising TypeError
        """
        result = _safe_float(value, default=0.0)
        assert result == 0.0
