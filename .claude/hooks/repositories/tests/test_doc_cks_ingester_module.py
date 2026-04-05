"""Tests for doc_cks_ingester.py module-based CKS CLI invocation.

This test file verifies that markdown files written to .claude/docs/ trigger
CKS ingest via module-based command invocation (sys.executable, -m, features.cks.cks_cli).

Run with:
    pytest P:/.claude/hooks/repositories/tests/test_doc_cks_ingester_module.py -v

TDD RED Phase: Test is expected to FAIL because current implementation uses
script path invocation, not module-based invocation.
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
# TEST CLASS: Module-based CKS CLI Command (Refactor Target)
# ============================================================================

class TestMarkdownIngestionTrigger:
    """Tests for module-based CKS CLI invocation (refactor from script path to -m module)."""

    def test_markdown_file_write_triggers_cks_ingest(self) -> None:
        """Verify writing a .md file to .claude/docs/ triggers CKS ingest via module invocation.

        Given: A markdown file is written to .claude/docs/ directory
        When: The file write event is detected
        Then: CKS ingest subprocess is called with module-based command format:
              sys.executable, "-m", "features.cks.cks_cli", "add", "--file", <path>

        This test verifies the refactor from direct script path invocation to
        Python module invocation (-m flag), which is more portable and follows
        Python best practices for CLI tools.

        Expected command format:
        - Uses sys.executable (current Python interpreter)
        - Uses "-m" flag to run module as script
        - Module path: "features.cks.cks_cli"
        - Subcommand: "add"
        - Flag: "--file"
        - Argument: <file_path>
        """
        on_file_written, _ = _import_doc_cks_ingester()

        # Arrange
        test_file_path = "P:/.claude/docs/test_document.md"
        test_content = "# Test Document\n\nThis is test content."

        # Act - Mock subprocess.run to capture the call
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Added to CKS",
                stderr=""
            )

            # Simulate file write event
            on_file_written(test_file_path, test_content)

            # Assert - subprocess.run should have been called
            assert mock_run.called, "subprocess.run should be called for .md files in docs directory"

            # Get the actual command that was called
            call_args = mock_run.call_args
            command = call_args[0][0] if call_args[0] else []

            # Assert - Verify command uses sys.executable (current Python interpreter)
            assert command[0] == sys.executable, \
                f"Command should use sys.executable, got: {command[0]}"

            # Assert - Verify command uses "-m" flag for module invocation
            assert command[1] == "-m", \
                f"Command should use '-m' flag for module invocation, got: {command[1]}"

            # Assert - Verify module path is "features.cks.cks_cli"
            assert command[2] == "features.cks.cks_cli", \
                f"Command should invoke module 'features.cks.cks_cli', got: {command[2]}"

            # Assert - Verify subcommand is "add"
            assert command[3] == "add", \
                f"Command should use 'add' subcommand, got: {command[3]}"

            # Assert - Verify --file flag
            assert command[4] == "--file", \
                f"Command should include '--file' flag, got: {command[4]}"

            # Assert - Verify file path is passed correctly
            assert command[5] == test_file_path, \
                f"Command should include file path, got: {command[5]}"

            # Final assertion - complete command format
            expected_command = [sys.executable, "-m", "features.cks.cks_cli", "add", "--file", test_file_path]
            assert command == expected_command, \
                f"Expected command: {expected_command}\nActual command: {command}"


# ============================================================================
# MAIN TEST SUITE ENTRY
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest when executed directly
    pytest.main([__file__, "-v"])
