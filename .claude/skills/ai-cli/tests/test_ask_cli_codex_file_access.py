"""
Integration tests for codex-cli file access with @file syntax support.

These tests verify that codex-cli can access files copied to P:/tmp/ via @file syntax.
Run with: pytest P:/.claude/skills/ai-cli/tests/test_ask_cli_codex_file_access.py -v
"""

# Add parent directory to path for imports
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import get_context


class TestCodexCliFileAccess:
    """Tests for codex-cli @file syntax file access."""

    @pytest.fixture
    def temp_file(self):
        r"""Create a temporary test file outside P:\ drive."""
        # Create temp file in user's temp directory (outside P:/)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_test_context.txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Test context content for codex-cli")
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

        # Cleanup any test files created
        # Note: We don't delete the directory itself as it may be used by other tests

    def test_codex_cli_file_access_via_at_syntax(self, temp_file, tmp_dir):
        """
        Test that codex-cli can access files copied to P:/tmp/ via @file syntax.

        Given: A file outside P:/ drive exists
        When: get_context() is called to copy file to P:/tmp/
        Then: Codex-cli should use @file syntax (consistent with qwen/gemini/vibe)
        """
        # Arrange
        original_content = temp_file.read_text(encoding="utf-8")
        original_filename = temp_file.name

        # Act - Copy file to P:/tmp/ using get_context
        context = get_context(str(temp_file), cli_name="codex")

        # Assert
        # 1. Context should use @file syntax (codex now consistent with other CLIs)
        assert context.startswith(
            "@"
        ), f"Codex should use @file syntax for consistency. Got: {context}"
        assert "P:/tmp/" in context, f"Codex @file syntax should reference P:/tmp/. Got: {context}"

        # 2. File should be copied to P:/tmp/ (referenced by @file syntax)
        tmp_file_path = tmp_dir / original_filename
        assert tmp_file_path.exists(), f"File should be copied to P:/tmp/ at {tmp_file_path}"

        # 3. Copied file should have same content as original
        copied_content = tmp_file_path.read_text(encoding="utf-8")
        assert copied_content == original_content, "Copied file content should match original"

        # 4. Context should NOT contain embedded content (only @file reference)
        assert (
            original_content not in context
        ), f"Codex should NOT embed content when using @file syntax. Got: {context}"

        # 5. Original file should still exist and be unchanged
        assert temp_file.exists(), "Original file should still exist"
        assert (
            temp_file.read_text(encoding="utf-8") == original_content
        ), "Original file content should be unchanged"

    def test_codex_cli_subprocess_receives_at_file_syntax(self, temp_file, tmp_dir):
        """
        Test that codex-cli subprocess receives @file syntax in query.

        Given: File has been copied to P:/tmp/ via get_context()
        When: codex-cli command is executed with @file context
        Then: Subprocess should receive query with @file syntax (consistent with other CLIs)
        """
        # Arrange
        original_content = temp_file.read_text(encoding="utf-8")

        # Get context with @file syntax (new codex behavior)
        context = get_context(str(temp_file), cli_name="codex")

        # Mock subprocess result
        mock_result = Mock()
        mock_result.stdout = '{"response": "AI response here"}'
        mock_result.stderr = ""
        mock_result.returncode = 0

        # Act - Mock subprocess.run to capture what codex-cli receives
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            import subprocess

            query = f"--- Context ---\n{context}\n---\nQuestion: Explain this code"
            result = subprocess.run(
                ["codex", "exec", "--json"], input=query, capture_output=True, text=True
            )

        # Assert - Verify subprocess.run was called with @file syntax
        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # The input should contain @file syntax, NOT embedded content
        subprocess_input = call_args[1]["input"]
        assert (
            "@P:/tmp/" in subprocess_input
        ), f"Codex subprocess should receive @file syntax. Got input: {subprocess_input}"
        assert context.startswith("@"), f"Context should use @file syntax. Got: {context}"

        # Verify the input does NOT contain embedded content (only @file reference)
        # Note: The @file syntax contains the filename, not the content
        assert (
            original_content not in subprocess_input or "@" in subprocess_input
        ), f"Input should use @file syntax, not embed content. Got: {subprocess_input}"

    def test_codex_cli_multiple_files_at_file_syntax(self, tmp_dir):
        """
        Test that codex-cli receives @file syntax for multiple files.

        Given: Multiple files outside P:/ drive
        When: get_context() is called with comma-separated file paths for codex
        Then: Context should use @file syntax for all files (consistent with qwen/gemini/vibe)
        """
        # Arrange - Create multiple test files outside P:/
        with tempfile.TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "test_file1.txt"
            file2 = Path(temp_dir) / "test_file2.py"
            file3 = Path(temp_dir) / "test_file3.md"

            file1.write_text("Content of file 1", encoding="utf-8")
            file2.write_text("print('Content of file 2')", encoding="utf-8")
            file3.write_text("# Content of file 3", encoding="utf-8")

            # Create comma-separated context source
            context_source = f"{file1},{file2},{file3}"

            # Act - Get context for codex (should use @file syntax)
            result = get_context(context_source, cli_name="codex")

            # Assert - All files should use @file syntax
            assert result, "Result should not be empty"

            # Verify @file syntax is used (space-separated @file references)
            assert result.count("@") == 3, "Codex should use @file syntax for all 3 files"
            assert "P:/tmp/" in result, "@file syntax should reference P:/tmp/"

            # Verify file names are in @file references
            assert "test_file1.txt" in result, "File 1 should be referenced with @file syntax"
            assert "test_file2.py" in result, "File 2 should be referenced with @file syntax"
            assert "test_file3.md" in result, "File 3 should be referenced with @file syntax"

            # Should NOT embed content or use === headers
            assert "===" not in result, "Codex should not use === headers with @file syntax"

            # Verify content is NOT embedded (only @file references)
            assert "Content of file 1" not in result, "File 1 content should NOT be embedded"
            assert (
                "print('Content of file 2')" not in result
            ), "File 2 content should NOT be embedded"
            assert "# Content of file 3" not in result, "File 3 content should NOT be embedded"

    def test_codex_cli_at_file_syntax_support_verification(self, temp_file, tmp_dir):
        """
        Test to verify codex-cli supports @file syntax for files in P:/tmp/.

        Given: A file copied to P:/tmp/
        When: Codex-cli is executed with @P:/tmp/filename syntax
        Then: Codex-cli should read and process the file content

        This test verifies the EXPECTED BEHAVIOR that codex-cli will support
        @file syntax for files in P:/tmp/ directory.

        THIS TEST SHOULD FAIL because codex-cli does not currently support @file syntax.
        """
        # Arrange
        original_content = temp_file.read_text(encoding="utf-8")

        # Copy file to P:/tmp/ using get_context
        context = get_context(str(temp_file), cli_name="codex")

        # Get the copied file path in P:/tmp/
        tmp_file_path = None
        for f in tmp_dir.glob(temp_file.name):
            tmp_file_path = f
            break

        assert tmp_file_path is not None, "File should be copied to P:/tmp/"

        # Verify the file was copied and has content
        assert tmp_file_path.exists(), f"Copied file should exist at {tmp_file_path}"
        copied_content = tmp_file_path.read_text(encoding="utf-8")
        assert copied_content == original_content, "Copied file should have original content"

        # Act & Assert - Verify get_context returns @file syntax for codex
        # As of the implementation, all CLIs (including codex) now use @file syntax
        result = get_context(str(temp_file), cli_name="codex")

        # Verify codex returns @file syntax (not embedded content)
        assert result.startswith("@"), (
            f"FAILED: Codex should use @file syntax for files in P:/tmp/, "
            f"but got: {result[:100]}"
        )

        # Verify the @file reference points to P:/tmp/
        assert (
            "P:/tmp/" in result
        ), f"FAILED: @file syntax should reference P:/tmp/ directory. Got: {result}"

        # Verify the result does NOT contain embedded content (only @file reference)
        assert original_content not in result, (
            f"FAILED: Codex should NOT embed content when using @file syntax. "
            f"Result contains embedded content: {result[:200]}"
        )
