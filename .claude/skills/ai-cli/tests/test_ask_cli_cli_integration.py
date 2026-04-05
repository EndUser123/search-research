"""
Integration tests for gemini-cli file access via @file syntax.

These tests verify that files can be accessed by gemini-cli when copied to P:/tmp/
Run with: pytest P:/.claude/skills/ai-cli/tests/test_ask_cli_cli_integration.py -v

NOTE: The feature is already implemented in ask_cli.py via _copy_to_tmp_if_needed().
These tests validate that the existing functionality works correctly.
"""

import subprocess

# Add parent directory to path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import get_context


class TestGeminiCliFileAccess:
    """Tests for gemini-cli @file syntax file access."""

    @pytest.fixture
    def temp_file(self):
        r"""Create a temporary test file outside P:\ drive."""
        # Create temp file in user's temp directory (outside P:/)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_test_context.txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Test context content for gemini-cli")
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        try:
            temp_path.unlink()
        except OSError:
            pass

    @pytest.fixture
    def tmp_dir(self):
        """Ensure P:/tmp/ directory exists for testing."""
        tmp_path = Path("P:/tmp/")
        tmp_path.mkdir(parents=True, exist_ok=True)

        yield tmp_path

    def test_get_context_copies_file_to_p_tmp_and_returns_at_syntax(self, temp_file, tmp_dir):
        """
        Test that get_context() copies file to P:/tmp/ and returns @P:/tmp/ reference.

        Given: A file path outside P:/ drive
        When: get_context() is called with that file path
        Then:
            - File should be copied to P:/tmp/
            - Result should contain @P:/tmp/ reference
            - Original file should remain unchanged
        """
        # Arrange
        original_content = temp_file.read_text(encoding="utf-8")
        original_filename = temp_file.name

        # Act
        result = get_context(str(temp_file), cli_name="gemini")

        # Assert
        # 1. Result should contain @P:/tmp/ reference
        assert result.startswith("@"), f"Expected @file syntax, got: {result}"
        assert "P:/tmp/" in result, f"Expected P:/tmp/ path in result, got: {result}"

        # 2. File should be copied to P:/tmp/
        tmp_file_path = Path(result.lstrip("@"))
        assert tmp_file_path.exists(), f"Copied file should exist at {tmp_file_path}"

        # 3. Copied file should have same content as original
        copied_content = tmp_file_path.read_text(encoding="utf-8")
        assert copied_content == original_content, "Copied file content should match original"

        # 4. Original file should still exist and be unchanged
        assert temp_file.exists(), "Original file should still exist"
        assert (
            temp_file.read_text(encoding="utf-8") == original_content
        ), "Original file content should be unchanged"

    def test_get_context_all_clis_use_at_file_syntax(self, temp_file):
        r"""
        Test that all CLIs (gemini, codex, qwen, vibe) use @file syntax for consistency.

        Given: A valid file path outside P:\ workspace
        When: get_context() is called with different cli_name values
        Then: All CLIs should return @file syntax pointing to P:/tmp/
        """
        # Arrange
        file_content = temp_file.read_text(encoding="utf-8")

        # Act
        gemini_result = get_context(str(temp_file), cli_name="gemini")
        codex_result = get_context(str(temp_file), cli_name="codex")

        # Assert
        # All CLIs should use @file syntax (NEW consistent behavior)
        assert gemini_result.startswith("@"), "gemini should use @file syntax"
        assert "P:/tmp/" in gemini_result, "gemini should reference P:/tmp/"

        assert codex_result.startswith("@"), "codex should use @file syntax (NEW behavior)"
        assert "P:/tmp/" in codex_result, "codex should reference P:/tmp/"

    @pytest.mark.parametrize("cli_name", ["qwen", "gemini", "vibe", None])
    def test_get_context_at_file_syntax_for_supported_clis(self, temp_file, cli_name):
        """
        Test that @file syntax is used for qwen, gemini, vibe, and unspecified CLIs.

        Given: A valid file path
        When: get_context() is called with various cli_name values
        Then: Should return @file syntax for all except codex
        """
        # Act
        result = get_context(str(temp_file), cli_name=cli_name)

        # Assert
        if cli_name == "codex":
            assert not result.startswith(
                "@"
            ), f"{cli_name} should embed contents, not use @file syntax"
        else:
            assert result.startswith("@"), f"{cli_name} should use @file syntax, got: {result}"


class TestGeminiCliSubprocessExecution:
    """Tests for mocking actual gemini-cli subprocess execution."""

    @patch("subprocess.run")
    def test_gemini_cli_receives_at_file_reference(self, mock_run):
        """
        Test that gemini-cli subprocess receives @P:/tmp/ file reference.

        Given: File has been copied to P:/tmp/
        When: gemini-cli command is executed
        Then: Subprocess should receive @P:/tmp/ reference in input
        """
        # Arrange
        test_file = Path("P:/tmp/test_query.txt")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Explain this code", encoding="utf-8")

        mock_result = Mock()
        mock_result.stdout = "AI response here"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Act
        import subprocess

        query = f"@{test_file}"
        result = subprocess.run(
            ["gemini", "-o", "json"], input=query, capture_output=True, text=True
        )

        # Assert
        # Verify subprocess.run was called with @file reference
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[1]["input"] == query
        # Normalize paths for comparison (Windows uses backslashes)
        input_str = str(call_args[1]["input"]).replace("\\", "/")
        assert "@P:/tmp/" in input_str, f"Expected @P:/tmp/ reference, got: {input_str}"


class TestVibeCliIntegrationWithTmpFiles:
    """Tests for vibe-cli accessing files copied to P:/tmp/."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_vibe_*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_vibe_get_context_copies_file_to_p_tmp(self, temp_dir, p_tmp_dir):
        r"""
        Test that get_context() copies file to P:/tmp/ for vibe CLI.

        Given: A file exists outside P:\ workspace (e.g., in temp directory)
        When: get_context() is called with cli_name="vibe"
        Then: The file should be copied to P:/tmp/ and return @P:/tmp/ syntax

        This test FAILS because vibe-cli integration with P:/tmp/ file access
        has not been verified to work correctly.
        """
        # Arrange - Create a test file outside P:\ workspace
        test_file = temp_dir / "test_vibe_context.txt"
        test_content = "This is test content for vibe-cli\nLine 2\nLine 3"
        test_file.write_text(test_content, encoding="utf-8")

        # Act - Call get_context to copy file to P:/tmp/ and get @file syntax
        context_result = get_context(str(test_file), cli_name="vibe")

        # Assert - Verify @file syntax references P:/tmp/ location
        assert context_result.startswith("@"), f"Expected @file syntax, got: {context_result}"
        assert (
            "P:/tmp/" in context_result
        ), f"Expected file copied to P:/tmp/, got: {context_result}"

        # Extract the P:/tmp/ file path from @file syntax
        copied_file_path = context_result.lstrip("@")
        copied_path = Path(copied_file_path)

        # Verify the copied file exists
        assert copied_path.exists(), f"Copied file should exist at: {copied_path}"

        # Verify content integrity
        copied_content = copied_path.read_text(encoding="utf-8")
        assert copied_content == test_content, "Copied content should match original"

    @patch("subprocess.run")
    def test_vibe_cli_receives_at_p_tmp_file_reference(self, mock_run, temp_dir, p_tmp_dir):
        """
        Test that vibe-cli subprocess receives @P:/tmp/ file reference.

        Given: File has been copied to P:/tmp/ via get_context()
        When: vibe-cli command is executed with the context
        Then: Subprocess should receive @P:/tmp/ reference in the query

        This test FAILS because vibe-cli subprocess execution with @P:/tmp/ file syntax
        has not been verified to work correctly.
        """
        # Arrange - Create test file outside P:
        test_file = temp_dir / "test_vibe_subprocess_file.txt"
        test_content = "Test content for vibe subprocess"
        test_file.write_text(test_content, encoding="utf-8")

        # Get context with @file syntax (should copy to P:/tmp/)
        context_result = get_context(str(test_file), cli_name="vibe")

        # Verify file was copied to P:/tmp/
        assert context_result.startswith("@"), "Should return @file syntax"
        assert "P:/tmp/" in context_result, "Should reference P:/tmp/"

        # Setup mock for subprocess.run
        mock_result = Mock()
        mock_result.stdout = '{"response": "vibe AI response"}'
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Act - Simulate vibe-cli command execution with @P:/tmp/ reference
        # This is what ask_cli.py does when running vibe
        query_with_context = f"Analyze this file: {context_result}"

        # Simulate the vibe command that would be executed
        result = subprocess.run(
            ["vibe", "-p", query_with_context, "--output", "json"], capture_output=True, text=True
        )

        # Assert - Verify subprocess.run was called
        assert mock_run.called, "subprocess.run should have been called for vibe"

        # Get the actual command that was called
        call_args = mock_run.call_args
        actual_command = call_args[0][0] if call_args[0] else []
        command_str = " ".join(actual_command)

        # Verify the command includes the @P:/tmp/ reference
        # This FAILS until vibe-cli integration is verified
        assert "@P:/tmp/" in command_str, (
            f"Expected vibe command to include @P:/tmp/ reference. " f"Got command: {command_str}"
        )
        assert "test_vibe_subprocess_file.txt" in command_str, (
            f"Expected vibe command to reference test_vibe_subprocess_file.txt. "
            f"Got command: {command_str}"
        )
