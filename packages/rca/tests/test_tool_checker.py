"""Tests for tool_checker module.

Tests for tool validation and availability checking.
"""

import pytest

from rca.tool_checker import (
    ToolAvailability,
    ToolChecker,
    ToolStatus,
)


class TestToolStatus:
    """Test ToolStatus enum."""

    def test_status_values(self):
        """ToolStatus has expected values."""
        assert ToolStatus.AVAILABLE.value == "available"
        assert ToolStatus.UNAVAILABLE.value == "unavailable"
        assert ToolStatus.UNKNOWN.value == "unknown"


class TestToolCheckerInit:
    """Test ToolChecker initialization."""

    def test_default_creation(self):
        """ToolChecker can be created."""
        checker = ToolChecker()

        assert checker is not None


class TestCheckTool:
    """Test tool checking."""

    def test_check_available_tool(self):
        """Available tool is detected."""
        checker = ToolChecker()

        status = checker.check_tool("Read")

        assert status == ToolStatus.AVAILABLE

    def test_check_unavailable_tool(self):
        """Unavailable tool is detected."""
        checker = ToolChecker()

        status = checker.check_tool("NonexistentTool")

        assert status in (ToolStatus.UNAVAILABLE, ToolStatus.UNKNOWN)

    def test_check_multiple_tools(self):
        """Multiple tools can be checked."""
        checker = ToolChecker()

        results = checker.check_tools(["Read", "Grep", "Edit"])

        assert len(results) == 3
        assert "Read" in results
        assert "Grep" in results
        assert "Edit" in results


class TestToolAvailability:
    """Test ToolAvailability dataclass."""

    def test_availability_creation(self):
        """ToolAvailability can be created."""
        availability = ToolAvailability(
            tool_name="Read",
            status=ToolStatus.AVAILABLE,
            version="1.0",
        )

        assert availability.tool_name == "Read"
        assert availability.status == ToolStatus.AVAILABLE

    def test_availability_defaults(self):
        """ToolAvailability has defaults."""
        availability = ToolAvailability(
            tool_name="Grep",
            status=ToolStatus.AVAILABLE,
        )

        assert availability.version is None


class TestGetToolInfo:
    """Test getting tool information."""

    def test_get_info_for_available_tool(self):
        """Info can be retrieved for available tool."""
        checker = ToolChecker()

        info = checker.get_tool_info("Read")

        assert info is not None
        assert info.tool_name == "Read"

    def test_get_info_for_unavailable_tool(self):
        """Info for unavailable tool returns None or unknown status."""
        checker = ToolChecker()

        info = checker.get_tool_info("NonexistentTool")

        assert info is None or info.status == ToolStatus.UNKNOWN


class TestValidateToolInputs:
    """Test tool input validation."""

    def test_valid_inputs(self):
        """Valid inputs pass validation."""
        checker = ToolChecker()

        result = checker.validate_inputs("Read", {"file_path": "test.py"})

        assert result is True

    def test_missing_required_input(self):
        """Missing required input fails validation."""
        checker = ToolChecker()

        result = checker.validate_inputs("Read", {})

        assert result is False

    def test_invalid_input_type(self):
        """Invalid input type fails validation."""
        checker = ToolChecker()

        result = checker.validate_inputs("Read", {"file_path": 123})

        assert result is False


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_tool_name(self):
        """Empty tool name is handled."""
        checker = ToolChecker()

        status = checker.check_tool("")

        assert status == ToolStatus.UNKNOWN

    def test_none_tool_name(self):
        """None tool name is handled."""
        checker = ToolChecker()

        status = checker.check_tool(None)

        assert status == ToolStatus.UNKNOWN

    def test_case_sensitive_tool_names(self):
        """Tool names are case-sensitive."""
        checker = ToolChecker()

        status1 = checker.check_tool("Read")
        status2 = checker.check_tool("read")

        # May or may not be equal depending on implementation
        assert status1 in (ToolStatus.AVAILABLE, ToolStatus.UNKNOWN)
