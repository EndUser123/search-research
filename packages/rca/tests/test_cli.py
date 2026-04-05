"""Tests for cli module.

Tests for CLI command handling and argument parsing.
"""

import pytest

from rca.cli import (
    CLICommand,
    CLIHandler,
)


class TestCLICommand:
    """Test CLICommand enum."""

    def test_command_values(self):
        """CLICommand has expected values."""
        assert CLICommand.ANALYZE.value == "analyze"
        assert CLICommand.REPORT.value == "report"
        assert CLICommand.HELP.value == "help"


class TestCLIHandlerInit:
    """Test CLIHandler initialization."""

    def test_handler_creation(self):
        """CLIHandler can be created."""
        handler = CLIHandler()

        assert handler is not None

    def test_handler_with_args(self):
        """Handler can be created with arguments."""
        handler = CLIHandler(args=["analyze", "--file", "test.py"])

        assert handler.args == ["analyze", "--file", "test.py"]


class TestParseCommand:
    """Test command parsing."""

    def test_parse_analyze_command(self):
        """Analyze command can be parsed."""
        handler = CLIHandler()

        command = handler.parse_command(["analyze", "--file", "test.py"])

        assert command == CLICommand.ANALYZE

    def test_parse_report_command(self):
        """Report command can be parsed."""
        handler = CLIHandler()

        command = handler.parse_command(["report", "--output", "report.md"])

        assert command == CLICommand.REPORT

    def test_parse_help_command(self):
        """Help command can be parsed."""
        handler = CLIHandler()

        command = handler.parse_command(["help"])

        assert command == CLICommand.HELP

    def test_parse_empty_args(self):
        """Empty args default to help."""
        handler = CLIHandler()

        command = handler.parse_command([])

        assert command == CLICommand.HELP


class TestExtractOptions:
    """Test option extraction."""

    def test_extract_file_option(self):
        """File option can be extracted."""
        handler = CLIHandler()

        options = handler.extract_options(["--file", "test.py", "--verbose"])

        assert options.get("file") == "test.py"
        assert options.get("verbose") is True

    def test_extract_output_option(self):
        """Output option can be extracted."""
        handler = CLIHandler()

        options = handler.extract_options(["--output", "result.json"])

        assert options.get("output") == "result.json"

    def test_extract_multiple_options(self):
        """Multiple options can be extracted."""
        handler = CLIHandler()

        options = handler.extract_options([
            "--file", "test.py",
            "--output", "report.md",
            "--verbose",
            "--format", "json",
        ])

        assert options.get("file") == "test.py"
        assert options.get("output") == "report.md"
        assert options.get("verbose") is True
        assert options.get("format") == "json"


class TestValidateOptions:
    """Test option validation."""

    def test_validate_valid_options(self):
        """Valid options pass validation."""
        handler = CLIHandler()

        is_valid = handler.validate_options({
            "file": "test.py",
            "output": "report.md",
        })

        assert is_valid is True

    def test_validate_missing_required(self):
        """Missing required option fails validation."""
        handler = CLIHandler()

        is_valid = handler.validate_options({
            # Missing 'file' which might be required
        })

        assert is_valid is False


class TestExecuteCommand:
    """Test command execution."""

    def test_execute_help_command(self):
        """Help command can be executed."""
        handler = CLIHandler()

        result = handler.execute_command(CLICommand.HELP)

        assert result is not None

    def test_execute_analyze_command(self):
        """Analyze command can be executed."""
        handler = CLIHandler()

        result = handler.execute_command(
            CLICommand.ANALYZE,
            options={"file": "test.py"}
        )

        assert result is not None


class TestGetUsageString:
    """Test usage string generation."""

    def test_get_usage_for_command(self):
        """Usage string can be retrieved for command."""
        handler = CLIHandler()

        usage = handler.get_usage(CLICommand.ANALYZE)

        assert usage is not None
        assert len(usage) > 0

    def test_get_general_usage(self):
        """General usage string can be retrieved."""
        handler = CLIHandler()

        usage = handler.get_usage()

        assert usage is not None
        assert len(usage) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_invalid_command(self):
        """Invalid command returns help."""
        handler = CLIHandler()

        command = handler.parse_command(["invalid_command"])

        assert command == CLICommand.HELP

    def test_none_args(self):
        """None args is handled."""
        handler = CLIHandler()

        command = handler.parse_command(None)

        assert command == CLICommand.HELP

    def test_empty_options(self):
        """Empty options dict is handled."""
        handler = CLIHandler()

        is_valid = handler.validate_options({})

        # May pass or fail depending on requirements
        assert isinstance(is_valid, bool)
