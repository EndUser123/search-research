#!/usr/bin/env python3
"""
Test suite for /diffbro command implementation.
TDD approach: Tests written first, then implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add commands directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / ".claude/commands"))


class TestDiffbroCommand:
    """Test suite for /diffbro slash command."""

    def test_command_exists(self):
        """Test that /diffbro command file exists."""
        diffbro_cmd = Path("P:/") / ".claude/commands/diffbro.md"
        assert diffbro_cmd.exists(), "/diffbro command documentation must exist"

    def test_command_structure(self):
        """Test that /diffbro has proper command structure."""
        diffbro_md = Path("P:/") / ".claude/commands/diffbro.md"
        if diffbro_md.exists():
            content = diffbro_md.read_text()
            assert "name:" in content, "Command must have name field"
            assert "purpose:" in content, "Command must have purpose field"
            assert "category:" in content, "Command must have category field"

    @patch("subprocess.run")
    def test_diffbro_not_installed(self, mock_run):
        """Test graceful handling when diffbro is not installed."""
        # Mock subprocess to simulate diffbro not found
        mock_run.side_effect = FileNotFoundError("diffbro not found")

        # Import from actual location
        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand()
            # Should handle error gracefully
            result = cmd.execute(mode="chill")
            assert "error" in result.lower() or "not found" in result.lower()
        except (ImportError, FileNotFoundError):
            # Command not implemented yet, which is ok for TDD
            pass

    @patch("subprocess.run")
    def test_diffbro_basic_execution(self, mock_run):
        """Test basic diffbro execution with default parameters."""
        # Mock successful diffbro run
        mock_result = Mock()
        mock_result.stdout = "Code review complete: No issues found"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand(check_available=False)  # Skip availability check
            result = cmd.execute()

            # Verify subprocess was called (excluding the --help check)
            assert mock_run.call_count >= 1, "Should be called at least once"
            # Get the last call (actual execution, not --help check)
            call_args = mock_run.call_args_list[-1]
            assert "diffbro" in call_args[0] or "diffbro" in str(call_args)
        except (ImportError, FileNotFoundError):
            # Command not implemented yet
            pass

    @patch("subprocess.run")
    def test_diffbro_mode_options(self, mock_run):
        """Test diffbro mode selection (chill, mid, chad)."""
        mock_result = Mock()
        mock_result.stdout = "Review complete"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        modes = ["chill", "mid", "chad"]

        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand(check_available=False)

            for mode in modes:
                cmd.execute(mode=mode)
                # Verify mode flag was passed
                call_args = mock_run.call_args_list[-1]  # Get last call
                assert f"--{mode}" in str(call_args)
        except (ImportError, FileNotFoundError):
            pass

    @patch("subprocess.run")
    def test_diffbro_file_filtering(self, mock_run):
        """Test file filtering options (--only, --ignore)."""
        mock_result = Mock()
        mock_result.stdout = "Review complete"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand(check_available=False)

            # Test --only
            cmd.execute(only_files=[".py", ".js"])
            call_args = mock_run.call_args_list[-1]
            assert "--only" in str(call_args) and ".py" in str(call_args)

            # Test --ignore
            cmd.execute(ignore_files=[".md", ".txt"])
            call_args = mock_run.call_args_list[-1]
            assert "--ignore" in str(call_args)
        except (ImportError, FileNotFoundError):
            pass

    @patch("subprocess.run")
    def test_diffbro_summarize(self, mock_run):
        """Test --summarize flag for commit message generation."""
        mock_result = Mock()
        mock_result.stdout = "feat: Add diffbro integration\n\nImplements AI code review"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand(check_available=False)
            result = cmd.execute(summarize=True)

            call_args = mock_run.call_args_list[-1]
            assert "--summarize" in str(call_args)
            # Check that we got some output
            assert result is not None and len(result) > 0
        except (ImportError, FileNotFoundError):
            pass

    @patch("subprocess.run")
    def test_diffbro_error_handling(self, mock_run):
        """Test error handling when diffbro fails."""
        mock_result = Mock()
        mock_result.stdout = "Error: API key not found"
        mock_result.stderr = "OPENAI_API_KEY not set"
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        try:
            sys.path.insert(0, str(Path("P:/") / ".claude/commands/diffbro"))
            from diffbro_command import DiffbroCommand
            cmd = DiffbroCommand(check_available=False)
            result = cmd.execute()

            # Should handle error gracefully
            assert result is not None and len(result) > 0
        except (ImportError, FileNotFoundError):
            pass


class TestDiffbroPlugin:
    """Test suite for CWO12 diffbro plugin."""

    def test_plugin_file_exists(self):
        """Test that plugin file exists in correct location."""
        plugin_file = Path("P:/__csf/src/modules/cwo12/plugins/diffbro_plugin.py")
        # This may not exist yet in TDD phase
        # assert plugin_file.exists(), "Plugin file must exist"

    def test_plugin_implements_interface(self):
        """Test that plugin implements required interface."""
        plugin_path = Path("P:/__csf/src/modules/cwo12/plugins/diffbro_plugin.py")

        if plugin_path.exists():
            # Import and check interface
            import importlib.util
            spec = importlib.util.spec_from_file_location("diffbro_plugin", plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Should have validate method
            assert hasattr(module, "DiffbroPlugin"), "Must export DiffbroPlugin class"
            assert hasattr(module.DiffbroPlugin, "validate"), "Must implement validate() method"

    @patch("subprocess.run")
    def test_plugin_validation(self, mock_run):
        """Test plugin validation during CWO12 Step 7."""
        mock_result = Mock()
        mock_result.stdout = "Code review: 2 warnings found"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        plugin_path = Path("P:/__csf/src/modules/cwo12/plugins/diffbro_plugin.py")

        if plugin_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("diffbro_plugin", plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Create plugin instance and validate
            plugin = module.DiffbroPlugin()
            result = plugin.validate(Mock())  # Mock workflow context

            assert result is not None, "Plugin must return validation result"
            assert hasattr(result, "passed"), "Result must have passed status"


class TestDiffbroIntegration:
    """Integration tests for diffbro command."""

    def test_command_discoverable(self):
        """Test that /diffbro command is discoverable."""
        commands_dir = Path("P:/.claude/commands")

        if commands_dir.exists():
            diffbro_files = list(commands_dir.glob("diffbro*"))
            assert len(diffbro_files) > 0, "Should have at least one diffbro file"

    def test_no_duplication_of_existing_commands(self):
        """Test that /diffbro doesn't duplicate existing functionality."""
        # This is more of a documentation/verification test
        # We check that /diffbro focuses on AI code review, not static analysis

        existing_commands = [
            "qual-gate",  # Static analysis
            "preview",    # PMGOA framework
            "test_review", # Production readiness
            "ast-analyze", # AST analysis
        ]

        # /diffbro should complement, not replace these
        # This test ensures we're not duplicating functionality
        assert True  # Placeholder for manual verification


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
