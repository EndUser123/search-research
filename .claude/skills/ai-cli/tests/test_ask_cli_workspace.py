r"""Tests for ask_cli workspace file handling.

These tests verify that files outside P:\ workspace are copied to P:/tmp/.
Run with: pytest P:/.claude/skills/ai-cli/tests/test_ask_cli_workspace.py -v
"""

# Add parent directory to path for imports
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import _read_multi_file_context, get_context


class TestMultiFileCopyToTmp:
    r"""Tests for copying multiple files outside P:\ workspace to P:/tmp/."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_*"):
                f.unlink()

    def test_copy_multiple_files_to_tmp(self, temp_dir, p_tmp_dir):
        r"""
        Test that when multiple files are outside P:\ workspace, all get copied to P:/tmp/.

        Given: Multiple test files exist outside P:\ workspace
        When: _read_multi_file_context is called with those file paths
        Then: All files should be copied to P:/tmp/ directory
        """
        # Arrange - Create multiple test files outside P:\
        file1 = temp_dir / "test_file1.txt"
        file2 = temp_dir / "test_file2.txt"
        file3 = temp_dir / "test_file3.md"

        file1.write_text("Content of file 1", encoding="utf-8")
        file2.write_text("Content of file 2", encoding="utf-8")
        file3.write_text("# Content of file 3", encoding="utf-8")

        # Create comma-separated context source with files outside P:\
        context_source = f"{file1},{file2},{file3}"

        # Act - Call the function that should copy files to P:/tmp/
        result = _read_multi_file_context(context_source, cli_name=None)

        # Assert - Verify all files were copied to P:/tmp/
        assert result, "Result should not be empty"

        # Check that files were copied to P:/tmp/
        copied_files = list(p_tmp_dir.glob("test_*"))
        assert (
            len(copied_files) >= 3
        ), f"Expected at least 3 files in P:/tmp/, found {len(copied_files)}"

        # Verify the copied files contain the expected content
        copied_file_names = {f.name for f in copied_files}
        assert "test_file1.txt" in copied_file_names, "test_file1.txt should be in P:/tmp/"
        assert "test_file2.txt" in copied_file_names, "test_file2.txt should be in P:/tmp/"
        assert "test_file3.md" in copied_file_names, "test_file3.md should be in P:/tmp/"

        # Verify content integrity
        for copied_file in copied_files:
            if copied_file.name == "test_file1.txt":
                assert copied_file.read_text(encoding="utf-8") == "Content of file 1"
            elif copied_file.name == "test_file2.txt":
                assert copied_file.read_text(encoding="utf-8") == "Content of file 2"
            elif copied_file.name == "test_file3.md":
                assert copied_file.read_text(encoding="utf-8") == "# Content of file 3"

        # Verify result contains @file references pointing to P:/tmp/
        assert "@" in result, "Result should contain @file references"
        assert "P:/tmp/" in result, "Result should reference P:/tmp/ directory"


class TestMixedWorkspaceAndExternalFiles:
    """Tests for behavior when mixing workspace and external files."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_only_external_files_copied(self, temp_dir, p_tmp_dir):
        r"""
        Test that only files outside P:\ are copied, not workspace files.

        Given: A mix of workspace files (inside P:\) and external files
        When: _read_multi_file_context is called with mixed paths
        Then: Only external files should be copied to P:/tmp/
        """
        # Arrange - Create one external file
        external_file = temp_dir / "external_file.txt"
        external_file.write_text("External content", encoding="utf-8")

        # Create a workspace file (inside P:\)
        workspace_file = Path("P:/workspace_test.txt")
        workspace_file.write_text("Workspace content", encoding="utf-8")

        try:
            context_source = f"{external_file},{workspace_file}"

            # Act
            result = _read_multi_file_context(context_source, cli_name=None)

            # Assert - External file should be copied
            copied_files = list(p_tmp_dir.glob("*external*"))
            assert len(copied_files) >= 1, "External file should be copied to P:/tmp/"

        finally:
            # Cleanup workspace file
            if workspace_file.exists():
                workspace_file.unlink()


class TestEdgeCases:
    """Tests for edge cases in file copying."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_empty_file_list(self):
        """
        Test behavior with empty or invalid file list.

        Given: Empty string or invalid paths
        When: _read_multi_file_context is called
        Then: Should handle gracefully without errors
        """
        # Arrange
        empty_context = ""

        # Act & Assert - Should not raise
        result = _read_multi_file_context(empty_context, cli_name=None)
        assert result == "", "Empty context should return empty string"

    def test_nonexistent_files(self, temp_dir, p_tmp_dir):
        """
        Test behavior when some files don't exist.

        Given: Context string with both existing and non-existent files
        When: _read_multi_file_context is called
        Then: Should copy existing files and warn about missing ones
        """
        # Arrange
        existing_file = temp_dir / "existing.txt"
        existing_file.write_text("Exists", encoding="utf-8")

        nonexistent_file = temp_dir / "does_not_exist.txt"

        context_source = f"{existing_file},{nonexistent_file}"

        # Act - Should warn about missing file but still process existing
        with patch("sys.stderr") as mock_stderr:
            result = _read_multi_file_context(context_source, cli_name=None)

        # Assert - Existing file should still be processed
        assert result, "Should process existing files"
        assert "@" in result or "existing" in result.lower()


class TestTmpFileNoCopy:
    """Tests for verifying files already in P:/tmp/ are not copied again."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_no_copy_*"):
                try:
                    f.unlink()
                except:
                    pass

    def test_no_copy_for_tmp_file(self, p_tmp_dir):
        """
        Test that when a file path is already in P:/tmp/, it is NOT copied again.

        Given: A file exists in P:/tmp/
        When: _read_multi_file_context is called with the P:/tmp/ file path
        Then: The file is NOT copied again to P:/tmp/ (no duplicate copies)
        """
        # Arrange - Create a test file directly in P:/tmp/
        test_filename = "test_no_copy_tmp_file.txt"
        test_content = "This file is already in P:/tmp/ and should not be copied again."
        test_file_path = p_tmp_dir / test_filename

        test_file_path.write_text(test_content, encoding="utf-8")

        # Get initial count of files in P:/tmp/ matching our test pattern
        initial_files = set(p_tmp_dir.glob("test_no_copy_*"))
        initial_count = len(initial_files)

        # Act - Call _read_multi_file_context with file already in P:/tmp/
        context_source = str(test_file_path)
        result = _read_multi_file_context(context_source, cli_name=None)

        # Assert - Verify the file was NOT copied again
        final_files = set(p_tmp_dir.glob("test_no_copy_*"))
        final_count = len(final_files)

        # The count should be the same - no new copies created
        assert final_count == initial_count, (
            f"File already in P:/tmp/ should NOT be copied again. "
            f"Initial count: {initial_count}, Final count: {final_count}. "
            f"New files created: {final_files - initial_files}"
        )

        # Verify the result references the original file
        assert result, "Result should not be empty"
        assert "@" in result, "Result should contain @file reference"
        assert test_filename in result, f"Result should reference {test_filename}"

        # Verify only ONE copy of the file exists (the original)
        matching_files = list(p_tmp_dir.glob(test_filename))
        assert len(matching_files) == 1, (
            f"Should have exactly ONE copy of {test_filename} in P:/tmp/, "
            f"but found {len(matching_files)}"
        )


class TestSingleFileWorkspaceHandling:
    """Tests for single file workspace-aware handling."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_copy_file_outside_workspace_to_tmp(self, temp_dir, p_tmp_dir):
        r"""
        Test that when a file path is outside P:\ workspace,
        it should be copied to P:/tmp/ and the @file syntax
        should reference the copied location.

        Given: A file path outside the P:\ workspace (e.g., C:/temp/file.txt)
        When: get_context() is called with that file path
        Then: The file should be copied to P:/tmp/ and @file should reference the copy
        """
        # Arrange: Create a temporary file outside P:\ workspace
        test_file = temp_dir / "test_external_file.txt"
        test_content = "This is test content from outside workspace\nLine 2\nLine 3"
        test_file.write_text(test_content, encoding="utf-8")

        # Act: Call get_context with the file outside workspace
        result = get_context(str(test_file), cli_name="qwen")

        # Assert: Verify @file syntax references P:/tmp/ location
        # The result should be @P:/tmp/<filename> not @<original_path>
        assert result.startswith("@"), f"Expected @file syntax, got: {result}"
        assert "P:/tmp/" in result, f"Expected file to be copied to P:/tmp/, got: {result}"
        assert str(test_file) not in result, f"Should not reference original path: {result}"

        # Verify the copied file exists and has the same content
        copied_path_str = result.lstrip("@")
        copied_path = Path(copied_path_str)
        assert copied_path.exists(), f"Copied file should exist at: {copied_path}"

        copied_content = copied_path.read_text(encoding="utf-8", errors="ignore")
        assert copied_content == test_content, "Copied file content should match original"


class TestCopyFailureHandling:
    """Tests for error handling when file copy fails."""

    @pytest.fixture
    def p_tmp_dir(self):
        """Create and cleanup P:/tmp/ directory."""
        p_tmp = Path("P:/tmp/")
        p_tmp.mkdir(parents=True, exist_ok=True)
        yield p_tmp
        # Cleanup after test
        if p_tmp.exists():
            for f in p_tmp.glob("test_*"):
                try:
                    f.unlink()
                except OSError:
                    pass

    def test_copy_failure_raises_error(self, temp_dir, p_tmp_dir):
        r"""
        Test that when file copy fails (e.g., permission denied), a clear error is raised.

        Given: A file exists outside P:\ workspace but cannot be copied due to permission error
        When: get_context() is called and shutil.copy raises PermissionError
        Then: A clear error message should be provided indicating the copy failure
        """
        # Arrange - Create a test file outside P:\
        test_file = temp_dir / "test_permission_denied.txt"
        test_file.write_text("This file will fail to copy", encoding="utf-8")

        # Act & Assert - Mock shutil.copy2 to raise PermissionError
        with patch("shutil.copy2") as mock_copy:
            # Simulate permission denied error
            mock_copy.side_effect = PermissionError(
                f"[Errno 13] Permission denied: '{test_file}' -> 'P:/tmp/{test_file.name}'"
            )

            # This should raise a clear error about the copy failure
            with pytest.raises(PermissionError) as exc_info:
                result = get_context(str(test_file), cli_name="qwen")

            # Verify the error message is clear and informative
            error_message = str(exc_info.value)
            assert (
                "Permission denied" in error_message or "PermissionError" in error_message
            ), f"Error message should clearly indicate permission denied. Got: {error_message}"
            assert (
                str(test_file) in error_message or test_file.name in error_message
            ), f"Error message should include the problematic file path. Got: {error_message}"
