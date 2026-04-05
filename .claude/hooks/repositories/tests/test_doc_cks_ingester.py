"""Tests for doc_cks_ingester.py automatic CKS ingestion on markdown file writes.
These tests verify that when .md files are written to the .claude/docs/ directory,
the CKS (Constitutional Knowledge System) ingest is automatically triggered via
subprocess call to the CKS CLI.
Run with:
    pytest P:/.claude/hooks/repositories/tests/test_doc_cks_ingester.py -v
TDD RED Phase: Tests are expected to FAIL because doc_cks_ingester.py
does not exist yet.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add repositories directory to path for imports
_repo_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_path))
# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def _import_doc_cks_ingester():
    """Import doc_cks_ingester module, raising ImportError if not found.
    Returns:
        tuple: (on_file_written, is_docs_path) functions or None
    Raises:
        ImportError: If doc_cks_ingester module doesn't exist yet
    """
    try:
        from doc_cks_ingester import is_docs_path, on_file_written
        return on_file_written, is_docs_path
    except ImportError as e:
        raise ImportError(
            f"doc_cks_ingester module not found: {e}"
            "\nThis is expected in RED phase - module will be created in GREEN phase."
        )
# ============================================================================
# TEST CLASS: Markdown File Write Triggers Ingest
# ============================================================================
class TestMarkdownFileWriteTriggersIngest:
    """Tests for automatic CKS ingestion when markdown files are written to docs directory."""
    def test_markdown_file_write_triggers_ingest(self) -> None:
        """Verify writing a .md file to .claude/docs/ triggers CKS ingest.
        Given: A markdown file is written to .claude/docs/ directory
        When: The file write event is detected
        Then: CKS ingest subprocess is called with correct file path and command format
        This is the core functionality test - ensuring that documentation updates
        automatically trigger knowledge base ingestion for semantic search.
        """
        on_file_written, is_docs_path = _import_doc_cks_ingester()
        # Arrange
        test_file_path = "P:/.claude/docs/test_document.md"
        test_content = "# Test Document\n\nThis is test content."
        # Act - Mock subprocess to verify CKS CLI is called correctly
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Added to CKS",
                stderr=""
            )
            # Simulate file write event
            on_file_written(test_file_path, test_content)
            # Assert - subprocess.run should have been called with CKS CLI command
            assert mock_run.called, "subprocess.run should be called for .md files in docs directory"
            # Verify the command format
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else call_args[1].get('args', [])
            # Command should include CKS CLI path and 'add' subcommand with --file flag
            assert any('cks_cli.py' in str(arg) for arg in command), \
                "Command should include cks_cli.py"
            assert any('add' in str(arg) for arg in command), \
                "Command should include 'add' subcommand"
            assert any('--file' in str(arg) or '-f' in str(arg) for arg in command), \
                "Command should include --file flag"
            assert test_file_path in command, \
                f"Command should include the file path: {test_file_path}"
    def test_markdown_file_in_nested_docs_directory_triggers_ingest(self) -> None:
        """Verify writing a .md file to nested .claude/docs/ paths triggers ingest.
        Given: A markdown file is written to .claude/docs/skills/ subdirectory
        When: The file write event is detected
        Then: CKS ingest subprocess is called (nested paths should also trigger)
        This ensures documentation in organized subdirectories is also ingested.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange
        nested_file_path = "P:/.claude/docs/skills/test_skill.md"
        test_content = "# Test Skill\n\nSkill documentation."
        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Added to CKS")
            on_file_written(nested_file_path, test_content)
            # Assert
            assert mock_run.called, "Nested docs paths should also trigger ingest"
    def test_markdown_file_write_to_non_docs_location_no_ingest(self) -> None:
        """Verify writing a .md file outside .claude/docs/ does NOT trigger ingest.
        Given: A markdown file is written to a location other than .claude/docs/
        When: The file write event is detected
        Then: CKS ingest subprocess is NOT called
        This prevents unnecessary ingestion of non-documentation markdown files
        (e.g., project README files, temporary notes, etc.)
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange
        non_docs_path = "P:/projects/other_project/README.md"
        test_content = "# README\n\nProject documentation."
        # Act
        with patch('subprocess.run') as mock_run:
            on_file_written(non_docs_path, test_content)
            # Assert - subprocess should NOT be called for non-docs paths
            assert not mock_run.called, \
                "subprocess.run should NOT be called for .md files outside .claude/docs/"
# ============================================================================
# TEST CLASS: Path Detection Helper
# ============================================================================
class TestIsDocsPath:
    """Tests for the is_docs_path helper function."""
    def test_is_docs_path_returns_true_for_docs_directory(self) -> None:
        """Verify is_docs_path returns True for paths within .claude/docs/.
        Given: A file path string
        When: The path is within .claude/docs/ directory
        Then: is_docs_path returns True
        Paths that should match:
        - P:/.claude/docs/file.md
        - P:/.claude/docs/subdir/file.md
        - .claude/docs/file.md (relative)
        """
        _, is_docs_path = _import_doc_cks_ingester()
        # Test various valid docs paths
        valid_paths = [
            "P:/.claude/docs/test.md",
            "P:/.claude/docs/skills/SKILL.md",
            "P:/.claude/docs/arch/ARCHITECTURE.md",
            ".claude/docs/test.md",  # Relative path
            "/.claude/docs/nested/deep/file.md",  # Absolute Unix-style
        ]
        for path in valid_paths:
            result = is_docs_path(path)
            assert result is True, \
                f"is_docs_path should return True for: {path}"
    def test_is_docs_path_returns_false_for_non_docs_directory(self) -> None:
        """Verify is_docs_path returns False for paths outside .claude/docs/.
        Given: A file path string
        When: The path is NOT within .claude/docs/ directory
        Then: is_docs_path returns False
        Paths that should NOT match:
        - P:/projects/README.md
        - P:/.claude/hooks/test.md
        - /tmp/test.md
        """
        _, is_docs_path = _import_doc_cks_ingester()
        # Test various invalid paths
        invalid_paths = [
            "P:/projects/README.md",
            "P:/.claude/hooks/test.md",
            "P:/.claude/skills/SKILL.md",
            "/tmp/test.md",
            "C:\\Users\\test.md",  # Windows absolute
            "README.md",  # Relative, no docs prefix
        ]
        for path in invalid_paths:
            result = is_docs_path(path)
            assert result is False, \
                f"is_docs_path should return False for: {path}"
    def test_is_docs_path_handles_windows_and_unix_paths(self) -> None:
        """Verify is_docs_path handles both Windows and Unix path separators.
        Given: A file path with either forward or backslash separators
        When: Checking if path is within .claude/docs/
        Then: Path detection works regardless of separator
        This ensures cross-platform compatibility.
        """
        _, is_docs_path = _import_doc_cks_ingester()
        # Windows-style path with backslashes
        windows_path = "P:\\.claude\\docs\\test.md"
        # Unix-style path with forward slashes
        unix_path = "P:/.claude/docs/test.md"
        # Both should be recognized as docs paths
        assert is_docs_path(windows_path) is True, \
            "Windows-style paths should be recognized"
        assert is_docs_path(unix_path) is True, \
            "Unix-style paths should be recognized"
# ============================================================================
# TEST CLASS: Non-Markdown Files
# ============================================================================
class TestNonMarkdownFiles:
    """Tests for handling non-markdown file types."""
    def test_non_markdown_files_ignored(self) -> None:
        """Verify .py, .txt, .json files do NOT trigger ingest, only .md files trigger.
        Given: Multiple file types are written (.py, .txt, .json, .md)
        When: Each file write event is processed
        Then:
            - .py, .txt, .json files should NOT trigger CKS ingest
            - Only .md files with matching paths SHOULD trigger ingest
        This test verifies the core file filtering behavior of doc_cks_ingester.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange: Test files with various extensions
        # Non-markdown files that should NOT trigger ingest
        non_markdown_files = [
            ("P:/.claude/docs/test_module.py", "def test(): pass"),
            ("P:/.claude/docs/config.txt", "configuration data"),
            ("P:/.claude/docs/data.json", '{"key": "value"}'),
        ]
        # Markdown files that SHOULD trigger ingest
        markdown_files = [
            ("P:/.claude/docs/README.md", "# README\n\nProject documentation."),
            ("P:/.claude/docs/guide.md", "# Guide\n\nUser guide content."),
        ]
        # Act & Assert: Non-markdown files should NOT trigger ingest
        for file_path, content in non_markdown_files:
            with patch('subprocess.run') as mock_run:
                on_file_written(file_path, content)
                # Assert - subprocess should NOT be called for non-.md files
                assert not mock_run.called, \
                    f"Writing {file_path} should NOT trigger CKS ingest (non-.md file)"
        # Act & Assert: Markdown files SHOULD trigger ingest
        for file_path, content in markdown_files:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Added to CKS",
                    stderr=""
                )
                on_file_written(file_path, content)
                # Assert - subprocess SHOULD be called for .md files
                assert mock_run.called, \
                    f"Writing {file_path} SHOULD trigger CKS ingest (.md file in docs path)"
                # Verify the command includes the file path
                call_args = mock_run.call_args
                command = call_args[0][0] if call_args[0] else call_args[1].get('args', [])
                assert file_path in str(command), \
                    f"Command should include the file path: {file_path}"
    def test_non_markdown_file_in_docs_no_ingest(self) -> None:
        """Verify writing non-.md files to docs directory does NOT trigger ingest.
        Given: A non-markdown file (e.g., .py, .txt, .json) is written to .claude/docs/
        When: The file write event is detected
        Then: CKS ingest subprocess is NOT called
        This ensures only markdown documentation files trigger ingestion.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Test various non-markdown file types
        test_cases = [
            ("P:/.claude/docs/test.py", "# Python code"),
            ("P:/.claude/docs/test.txt", "Plain text"),
            ("P:/.claude/docs/test.json", '{"key": "value"}'),
            ("P:/.claude/docs/image.png", b"binary data"),
        ]
        for file_path, content in test_cases:
            with patch('subprocess.run') as mock_run:
                on_file_written(file_path, content)
                # Assert - subprocess should NOT be called for non-markdown files
                assert not mock_run.called, \
                    f"subprocess.run should NOT be called for non-.md files: {file_path}"
# ============================================================================
# TEST CLASS: Subprocess Command Format
# ============================================================================
class TestSubprocessCommandFormat:
    """Tests for verifying correct CKS CLI command format."""
    def test_subprocess_command_format_correct(self) -> None:
        """Verify subprocess call uses correct CKS CLI command format.
        Given: A markdown file write to .claude/docs/
        When: The ingest subprocess is executed
        Then: Command follows format: python cks_cli.py add --file <path>
        Expected command format:
        - Uses python executable
        - Calls cks_cli.py from __csf/src/cli/
        - Uses 'add' subcommand
        - Includes '--file' flag with file path argument
        """
        on_file_written, _ = _import_doc_cks_ingester()
        test_file_path = "P:/.claude/docs/test.md"
        test_content = "# Test"
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            on_file_written(test_file_path, test_content)
            # Get the actual command called
            call_args = mock_run.call_args
            if call_args[0]:
                command = call_args[0][0]
                if isinstance(command, list):
                    command_str = " ".join(str(arg) for arg in command)
                else:
                    command_str = str(command)
            else:
                # Command might be in kwargs
                command = call_args[1].get('args', [])
                command_str = " ".join(str(arg) for arg in command) if isinstance(command, list) else str(command)
            # Verify command components
            assert 'python' in command_str.lower(), \
                "Command should use python executable"
            assert 'cks_cli.py' in command_str, \
                "Command should include cks_cli.py"
            assert 'add' in command_str, \
                "Command should include 'add' subcommand"
            assert '--file' in command_str or '-f' in command_str, \
                "Command should include --file flag"
            assert test_file_path in command_str, \
                f"Command should include file path: {test_file_path}"
    def test_subprocess_call_includes_capture_output(self) -> None:
        """Verify subprocess call includes output capture parameters.
        Given: CKS ingest subprocess is called
        When: The subprocess.run( is executed
        Then: capture_output=True or equivalent parameters are included
        This ensures CKS CLI output is captured for logging/debugging.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            on_file_written("P:/.claude/docs/test.md", "# Test")
            # Verify capture_output or equivalent is in the call
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs.get('capture_output') or call_kwargs.get('stdout') or call_kwargs.get('stderr'), \
                "subprocess.run should capture output for logging"
    def test_subprocess_failure_handling(self) -> None:
        """Verify subprocess failures are handled gracefully.
        Given: CKS CLI command fails (non-zero return code)
        When: The subprocess.run( returns an error
        Then: Error is logged/handled without crashing
        This ensures CKS ingestion failures don't break the file write operation.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Mock a failing subprocess
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,  # Non-zero = error
                stdout="",
                stderr="CKS ingestion failed"
            )
            # Should not raise exception
            on_file_written("P:/.claude/docs/test.md", "# Test")
            # Verify it was called (error handling happens internally)
            assert mock_run.called
# ============================================================================
# TEST CLASS: Edge Cases
# ============================================================================
class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    def test_empty_file_content_still_triggers_ingest(self) -> None:
        """Verify writing an empty .md file still triggers ingest.
        Given: An empty markdown file is written to .claude/docs/
        When: The file write event is detected
        Then: CKS ingest subprocess is still called (empty files are valid)
        Edge case: Empty documentation files should still be indexed.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        with patch('subprocess.run') as mock_run:
            on_file_written("P:/.claude/docs/empty.md", "")
            assert mock_run.called, "Empty files should still trigger ingest"
    def test_path_with_special_characters(self) -> None:
        """Verify paths with special characters are handled correctly.
        Given: A file path with spaces, underscores, or special characters
        When: The file write event is detected
        Then: Path is properly escaped/quoted in subprocess call
        Edge case: Documentation files might have names like "API Reference.md"
        """
        on_file_written, _ = _import_doc_cks_ingester()
        special_paths = [
            "P:/.claude/docs/API Reference.md",
            "P:/.claude/docs/v2.0_release-notes.md",
            "P:/.claude/docs/test_file (copy).md",
        ]
        for path in special_paths:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                # Should not raise exception
                on_file_written(path, "# Test")
                # Verify subprocess was called
                assert mock_run.called, \
                    f"Files with special characters should be handled: {path}"
    def test_none_file_content_graceful_handling(self) -> None:
        """Verify None file content is handled gracefully.
        Given: File write event with None content
        When: The event is processed
        Then: Handled gracefully (either skip or treat as empty)
        Edge case: Some file watchers might pass None for content.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Should handle None content gracefully
        with patch('subprocess.run') as mock_run:
            # Either skip (no subprocess call) or proceed with empty content
            on_file_written("P:/.claude/docs/test.md", None)
            # Implementation can choose to skip or proceed
            # Either behavior is acceptable for this edge case
class TestExcludedPatterns:
    """Tests for excluded markdown file patterns that should NOT trigger ingest."""
    def test_excluded_patterns_not_ingested(self) -> None:
        """Verify files matching excluded patterns do NOT trigger CKS ingest.
        Given: Files matching patterns *_temp*.md, *_draft*.md, *.tmp.md
        When: These files are written to .claude/docs/ directory
        Then: CKS ingest subprocess is NOT called
        Excluded patterns represent temporary/draft documentation that should
        not be indexed in the knowledge base:
        - *_temp*.md: Temporary working files (e.g., design_temp_v1.md)
        - *_draft*.md: Draft documents not ready for indexing (e.g., api_draft.md)
        - *.tmp.md: Temporary marker files (e.g., notes.tmp.md)
        This prevents cluttering the knowledge base with transient content.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange: Test files matching excluded patterns
        excluded_files = [
            # *_temp*.md pattern
            ("P:/.claude/docs/design_temp_v1.md", "# Temporary Design"),
            ("P:/.claude/docs/notes_temp_backup.md", "# Backup notes"),

            # *_draft*.md pattern
            ("P:/.claude/docs/api_draft.md", "# Draft API docs"),
            ("P:/.claude/docs/guide_draft_v2.md", "# Draft guide"),

            # *.tmp.md pattern
            ("P:/.claude/docs/scratch.tmp.md", "# Scratch notes"),
            ("P:/.claude/docs/workfile.tmp.md", "# Temporary work"),
        ]
        # Act & Assert: None of the excluded files should trigger ingest
        for file_path, content in excluded_files:
            with patch('subprocess.run') as mock_run:
                on_file_written(file_path, content)
                # Assert - subprocess should NOT be called for excluded patterns
                assert not mock_run.called, f"File {file_path} matches excluded pattern and should NOT trigger CKS ingest"
    def test_similar_non_excluded_files_still_ingested(self) -> None:
        """Verify files that look similar but don't match excluded patterns DO trigger ingest.
        Given: Files with similar names but NOT matching excluded patterns
        When: These files are written to .claude/docs/ directory
        Then: CKS ingest subprocess IS called
        This ensures the exclusion patterns are precise and don't over-block.
        Valid files that should still be ingested:
        - temperature.md (no _temp prefix)
        - drafty.md (no _draft suffix)
        - template.md (no .tmp prefix)
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange: Test files that look similar but should NOT be excluded
        should_be_ingested = [
            # "temp" in middle or end is OK
            ("P:/.claude/docs/temperature.md", "# Temperature settings"),
            ("P:/.claude/docs/itemplate.md", "# Item plate docs"),

            # "draft" without _ prefix is OK
            ("P:/.claude/docs/drafty.md", "# Drafty content"),
            ("P:/.claude/docs/drafting_guide.md", "# How to draft"),

            # "tmp" without . prefix is OK
            ("P:/.claude/docs/atmple.md", "# ATMple example"),
            ("P:/.claude/docs/template.md", "# Template file"),
        ]
        # Act & Assert: These similar files SHOULD trigger ingest
        for file_path, content in should_be_ingested:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Added to CKS",
                    stderr=""
                )
                on_file_written(file_path, content)
                # Assert - subprocess SHOULD be called for non-excluded files
                assert mock_run.called, f"File {file_path} does NOT match excluded pattern and SHOULD trigger CKS ingest"
    def test_excluded_patterns_with_nested_paths(self) -> None:
        """Verify excluded patterns work correctly in nested docs directories.
        Given: Files matching excluded patterns in nested .claude/docs/ subdirectories
        When: These files are written
        Then: CKS ingest subprocess is NOT called
        Ensures exclusion patterns work at any directory depth within docs/.
        Excluded patterns:
        - *_temp*.md: underscore, "temp", anything, .md (e.g., notes_temp.md, work_temp_v1.md)
        - *_draft*.md: underscore, "draft", anything, .md (e.g., api_draft.md, design_draft_v2.md)
        - *.tmp.md: anything, ".tmp.md" (e.g., scratch.tmp.md, notes.tmp.md)
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange: Excluded files in nested directories
        nested_excluded = [
            # *_temp*.md pattern - underscore + temp + anything + .md
            ("P:/.claude/docs/skill/learning_temp.md", "# Temp skill"),
            ("P:/.claude/docs/arch/design_temp_v1.md", "# Draft design temp"),
            # *_draft*.md pattern - underscore + draft + anything + .md
            ("P:/.claude/docs/api/reference_draft.md", "# Draft reference"),
            ("P:/.claude/docs/arch/design_draft_v2.md", "# Draft design v2"),
            # *.tmp.md pattern - anything + .tmp.md
            ("P:/.claude/docs/api/notes.tmp.md", "# Temp notes"),
            ("P:/.claude/docs/work/scratch.tmp.md", "# Scratch work"),
        ]
        # Act & Assert
        for file_path, content in nested_excluded:
            with patch('subprocess.run') as mock_run:
                on_file_written(file_path, content)
                assert not mock_run.called, f"Nested excluded file {file_path} should NOT trigger CKS ingest"
# ============================================================================
# TEST CLASS: Non-Blocking Behavior
# ============================================================================
class TestNonBlockingBehavior:
    """Tests for verifying that CKS CLI subprocess failures don't block write operations.
    These tests verify that when the CKS ingestion subprocess fails (either by
    returning a non-zero exit code or raising an exception), the file write
    operation is allowed to proceed. This is critical for user experience -
    documentation updates should never be blocked by CKS ingestion issues.
    """
    def test_subprocess_failure_doesnt_block_write(self) -> None:
        """Verify subprocess exceptions don't block the write operation (non-blocking behavior).
        Given: A markdown file is written to .claude/docs/ directory
        When: The CKS CLI subprocess.run( raises an exception (e.g., FileNotFoundError, TimeoutExpired)
        Then:
            - The hook returns empty JSON {} (allowing write to proceed)
            - Exception is handled gracefully (logged but doesn't propagate)
            - on_file_written() completes without raising an exception
        This is a critical test for ensuring that CKS ingestion failures are
        non-blocking - users should always be able to save their documentation
        even if the CKS system is unavailable or experiencing issues.
        The non-blocking behavior is achieved by catching all exceptions in
        trigger_cks_ingest() and logging them without re-raising.
        """
        on_file_written, _ = _import_doc_cks_ingester()
        # Arrange
        test_file_path = "P:/.claude/docs/test_document.md"
        test_content = "# Test Document\n\nThis is test content."
        # Act - Mock subprocess.run to raise an exception
        # This simulates CKS CLI being unavailable or failing catastrophically
        with patch('subprocess.run') as mock_run:
            # Simulate CKS CLI not found or other critical failure
            mock_run.side_effect = FileNotFoundError("CKS CLI not found")
            # This should NOT raise an exception - the error is handled internally
            # The function should complete successfully, allowing the write to proceed
            on_file_written(test_file_path, test_content)
            # Assert - subprocess.run was called (attempt was made)
            assert mock_run.called, "subprocess.run should be attempted"
            # The key assertion: on_file_written completed without propagating the exception
            # If this line is reached, the exception was handled gracefully
        # Additional test case: Verify TimeoutExpired is also handled gracefully
        with patch('subprocess.run') as mock_run:
            # Simulate CKS CLI timeout
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired(
                "python", 10
            )
            # Should NOT raise - timeout is handled internally
            on_file_written(test_file_path, test_content)
            assert mock_run.called, "subprocess.run should be attempted"
        # Additional test case: Verify generic exceptions are also handled
        with patch('subprocess.run') as mock_run:
            # Simulate any unexpected exception
            mock_run.side_effect = RuntimeError("Unexpected CKS CLI error")
            # Should NOT raise - all exceptions are caught and logged
            on_file_written(test_file_path, test_content)
            assert mock_run.called, "subprocess.run should be attempted"
# ============================================================================
# TEST CLASS: Non-Markdown Files Ignored (should_ingest pattern)
# ============================================================================
class TestNonMarkdownIgnored:
    """Tests for verifying non-.md files (.py, .txt, .json) are ignored and do NOT trigger CKS ingest.
    These tests verify the should_ingest function pattern correctly filters file types,
    ensuring only markdown files trigger automatic CKS ingestion regardless of directory.
    """
    def test_python_file_not_ingested(self) -> None:
        """Verify .py files do NOT trigger CKS ingest.
        Given: A Python file (.py) is written to a monitored directory (.claude/docs/)
        When: The file write event is processed through should_ingest
        Then: 
            - should_ingest returns False for .py files
            - subprocess.run is NOT called for .py files
            - No CKS ingestion is triggered
        This ensures Python source code files don't trigger documentation indexing.
        """
        from doc_cks_ingester import should_ingest
        # Arrange
        python_file_path = "P:/.claude/docs/test_module.py"
        test_content = 'def test():\n    pass'
        # Act - Verify should_ingest returns False for .py files
        result = should_ingest(python_file_path)
        # Assert - should_ingest should return False for non-.md files
        assert result is False,             f"should_ingest should return False for .py files, got: {result}"
        # Act & Assert - Verify subprocess.run is NOT called when writing .py file
        with patch('subprocess.run') as mock_run:
            on_file_written, _ = _import_doc_cks_ingester()
            on_file_written(python_file_path, test_content)
            # subprocess.run should NOT be called for .py files
            assert not mock_run.called,                 f"subprocess.run should NOT be called for .py files: {python_file_path}"
    def test_text_file_not_ingested(self) -> None:
        """Verify .txt files do NOT trigger CKS ingest.
        Given: A text file (.txt) is written to a monitored directory (.claude/docs/)
        When: The file write event is processed through should_ingest
        Then: 
            - should_ingest returns False for .txt files
            - subprocess.run is NOT called for .txt files
            - No CKS ingestion is triggered
        This ensures plain text files don't trigger documentation indexing.
        """
        from doc_cks_ingester import should_ingest
        # Arrange
        text_file_path = "P:/.claude/docs/config.txt"
        test_content = "configuration data"
        # Act - Verify should_ingest returns False for .txt files
        result = should_ingest(text_file_path)
        # Assert - should_ingest should return False for non-.md files
        assert result is False,             f"should_ingest should return False for .txt files, got: {result}"
        # Act & Assert - Verify subprocess.run is NOT called when writing .txt file
        with patch('subprocess.run') as mock_run:
            on_file_written, _ = _import_doc_cks_ingester()
            on_file_written(text_file_path, test_content)
            # subprocess.run should NOT be called for .txt files
            assert not mock_run.called,                 f"subprocess.run should NOT be called for .txt files: {text_file_path}"
    def test_json_file_not_ingested(self) -> None:
        """Verify .json files do NOT trigger CKS ingest.
        Given: A JSON file (.json) is written to a monitored directory (.claude/docs/)
        When: The file write event is processed through should_ingest
        Then: 
            - should_ingest returns False for .json files
            - subprocess.run is NOT called for .json files
            - No CKS ingestion is triggered
        This ensures JSON configuration/data files don't trigger documentation indexing.
        """
        from doc_cks_ingester import should_ingest
        # Arrange
        json_file_path = "P:/.claude/docs/data.json"
        test_content = '{"key": "value"}'
        # Act - Verify should_ingest returns False for .json files
        result = should_ingest(json_file_path)
        # Assert - should_ingest should return False for non-.md files
        assert result is False,             f"should_ingest should return False for .json files, got: {result}"
        # Act & Assert - Verify subprocess.run is NOT called when writing .json file
        with patch('subprocess.run') as mock_run:
            on_file_written, _ = _import_doc_cks_ingester()
            on_file_written(json_file_path, test_content)
            # subprocess.run should NOT be called for .json files
            assert not mock_run.called,                 f"subprocess.run should NOT be called for .json files: {json_file_path}"


# ============================================================================
# TEST CLASS: Whitelisted Paths
# ============================================================================

class TestWhitelistedPaths:
    """Tests for whitelisted .claude/ path filtering.

    These tests verify that only the specific whitelisted .claude/ paths
    trigger CKS ingestion (.claude/docs/, .claude/hooks/, .claude/agents/),
    while other paths like __csf/docs/ do not trigger ingestion.
    """

    def test_claude_docs_path_ingested(self) -> None:
        """Verify .claude/docs/ paths trigger CKS ingest.

        Given: A markdown file is written to .claude/docs/ directory
        When: The file write event is detected
        Then: CKS ingest subprocess IS called

        This verifies the .claude/docs/ path is in the whitelist.
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange
        test_file_path = "P:/.claude/docs/test_document.md"
        test_content = "# Test Document\n\nThis is test content."

        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Added to CKS",
                stderr=""
            )

            on_file_written(test_file_path, test_content)

            # Assert - subprocess SHOULD be called for .claude/docs/
            assert mock_run.called, \
                "subprocess.run should be called for .md files in .claude/docs/"

            # Verify the command includes the file path
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else call_args[1].get('args', [])
            assert test_file_path in str(command), \
                f"Command should include the file path: {test_file_path}"

    def test_claude_hooks_path_ingested(self) -> None:
        """Verify .claude/hooks/ paths trigger CKS ingest.

        Given: A markdown file is written to .claude/hooks/ directory
        When: The file write event is detected
        Then: CKS ingest subprocess IS called

        This verifies the .claude/hooks/ path is in the whitelist.
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange
        test_file_path = "P:/.claude/hooks/CLAUDE.md"
        test_content = "# Hooks Documentation\n\nHook reference."

        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Added to CKS",
                stderr=""
            )

            on_file_written(test_file_path, test_content)

            # Assert - subprocess SHOULD be called for .claude/hooks/
            assert mock_run.called, \
                "subprocess.run should be called for .md files in .claude/hooks/"

            # Verify the command includes the file path
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else call_args[1].get('args', [])
            assert test_file_path in str(command), \
                f"Command should include the file path: {test_file_path}"

    def test_claude_agents_path_ingested(self) -> None:
        """Verify .claude/agents/ paths trigger CKS ingest.

        Given: A markdown file is written to .claude/agents/ directory
        When: The file write event is detected
        Then: CKS ingest subprocess IS called

        This verifies the .claude/agents/ path is in the whitelist.
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange
        test_file_path = "P:/.claude/agents/AGENT.md"
        test_content = "# Agent Documentation\n\nAgent behavior reference."

        # Act
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Added to CKS",
                stderr=""
            )

            on_file_written(test_file_path, test_content)

            # Assert - subprocess SHOULD be called for .claude/agents/
            assert mock_run.called, \
                "subprocess.run should be called for .md files in .claude/agents/"

            # Verify the command includes the file path
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else call_args[1].get('args', [])
            assert test_file_path in str(command), \
                f"Command should include the file path: {test_file_path}"

    def test_other_docs_path_not_ingested(self) -> None:
        """Verify non-whitelisted docs paths do NOT trigger CKS ingest.

        Given: A markdown file is written to a non-whitelisted path (e.g., __csf/docs/)
        When: The file write event is detected
        Then: CKS ingest subprocess is NOT called

        This verifies that only the specific whitelisted .claude/ paths
        trigger ingestion, and other docs-like paths are excluded.

        Test cases:
        - __csf/docs/ (external CSF documentation)
        - .csf/docs/ (similar but not whitelisted)
        - docs/ (root-level docs)
        - .other/docs/ (other dot-directory docs)
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange: Test files in non-whitelisted docs paths
        non_whitelisted_paths = [
            ("P:/__csf/docs/reference.md", "# CSF Reference"),
            ("P:/.csf/docs/guide.md", "# CSF Guide"),
            ("P:/docs/readme.md", "# Root Docs"),
            ("P:/.other/docs/test.md", "# Other Docs"),
            ("P:/projects/some-docs/docs/file.md", "# Project Docs"),
        ]

        # Act & Assert: None of the non-whitelisted paths should trigger ingest
        for file_path, content in non_whitelisted_paths:
            with patch('subprocess.run') as mock_run:
                on_file_written(file_path, content)

                # Assert - subprocess should NOT be called for non-whitelisted paths
                assert not mock_run.called, \
                    f"File {file_path} is NOT in whitelisted paths and should NOT trigger CKS ingest"

    def test_nested_whitelisted_paths_ingested(self) -> None:
        """Verify nested paths within whitelisted directories trigger ingest.

        Given: A markdown file is written to a nested subdirectory of a whitelisted path
        When: The file write event is detected
        Then: CKS ingest subprocess IS called

        This ensures that whitelisting applies recursively to all nested paths.

        Test cases:
        - .claude/docs/skills/test.md (nested skills)
        - .claude/hooks/repositories/test.md (nested repositories)
        - .claude/agents/specialized/test.md (nested agents)
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange: Test files in nested whitelisted paths
        nested_whitelisted_paths = [
            ("P:/.claude/docs/skills/SKILL.md", "# Skill Doc"),
            ("P:/.claude/docs/arch/ARCHITECTURE.md", "# Architecture"),
            ("P:/.claude/hooks/repositories/test.md", "# Repository Hook"),
            ("P:/.claude/agents/specialized/AGENT.md", "# Specialized Agent"),
        ]

        # Act & Assert: All nested whitelisted paths should trigger ingest
        for file_path, content in nested_whitelisted_paths:
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Added to CKS",
                    stderr=""
                )

                on_file_written(file_path, content)

                # Assert - subprocess SHOULD be called for nested whitelisted paths
                assert mock_run.called, \
                    f"File {file_path} is in a nested whitelisted path and SHOULD trigger CKS ingest"


# ============================================================================
# MAIN TEST SUITE ENTRY
# ============================================================================
if __name__ == "__main__":
    # Run tests with pytest when executed directly
    pytest.main([__file__, "-v"])
