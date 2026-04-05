#!/usr/bin/env python3
"""
Test suite for post-Bash Python file syntax validation.

This test suite validates the check_python_file_edits() function that
detects and validates Python files modified by Bash commands.

Tests follow the RED-GREEN-REFACTOR TDD cycle.
Run with: python -m pytest P:/.claude/hooks/tests/test_bash_syntax_validation.py -v
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add hooks lib to path
hooks_lib = Path(__file__).resolve().parent.parent / "__lib"
sys.path.insert(0, str(hooks_lib))

from pre_tool_use_logic import check_python_file_edits


class TestBashSyntaxValidation:
    """Test suite for check_python_file_edits() function."""

    def setup_method(self):
        """Create a temporary git repo for testing."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_bash_syntax_")
        self.original_cwd = os.getcwd()

        # Initialize git repo
        subprocess.run(
            ["git", "init"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Test 1: Happy Path - Bash command that doesn't modify .py files
    def test_no_py_files_modified(self):
        """When Bash command doesn't modify .py files, allow the operation."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "tool_response": {"stdout": "file.txt\n"}
        }

        result = check_python_file_edits(data)

        assert result is None, "Should allow when no .py files changed"

    # Test 2: Syntax Error - Bash command creates invalid .py file
    def test_syntax_error_blocks(self):
        """When Bash command creates .py file with syntax error, block with error message."""
        # Create a .py file with syntax error
        bad_file = Path(self.temp_dir) / "bad.py"
        bad_file.write_text("""
def foo():
    print("hello")
  print("indented wrong")  # IndentationError
""")

        # Add to git so it shows in diff
        subprocess.run(
            ["git", "add", "bad.py"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test", "cwd": self.temp_dir},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        assert result is not None, "Should block when syntax error found"
        assert result["decision"] == "block", "Should block the operation"
        assert "syntax error" in result["message"].lower(), "Should mention syntax error"
        assert "bad.py" in result["message"], "Should identify the problematic file"

    # Test 3: Multiple Files - Bash command modifies 3 .py files, 1 has error
    def test_multiple_files_one_error(self):
        """When Bash modifies multiple .py files and one has error, block with specific file."""
        # Create valid files
        (Path(self.temp_dir) / "good1.py").write_text("print('good1')\n")
        (Path(self.temp_dir) / "good2.py").write_text("print('good2')\n")

        # Create file with syntax error (mixed indentation)
        bad_file = Path(self.temp_dir) / "bad.py"
        bad_file.write_text("def foo():\n    print('correct')\n  print('wrong')  # IndentationError\n")

        # Add all to git
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test", "cwd": self.temp_dir},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        assert result is not None, "Should block when any file has syntax error"
        assert result["decision"] == "block", "Should block the operation"
        assert "bad.py" in result["message"], "Should identify the problematic file"

    # Test 4: New File - Bash command creates new .py file with valid syntax
    def test_new_valid_file_allowed(self):
        """When Bash creates new .py file with valid syntax, allow the operation."""
        new_file = Path(self.temp_dir) / "new_valid.py"
        new_file.write_text("""
def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()
""")

        # Add to git so it shows in diff
        subprocess.run(
            ["git", "add", "new_valid.py"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test", "cwd": self.temp_dir},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        assert result is None, "Should allow when new file has valid syntax"

    # Test 5: New File Error - Bash command creates new .py file with syntax error
    def test_new_invalid_file_blocked(self):
        """When Bash creates new .py file with syntax error, block with error message."""
        new_file = Path(self.temp_dir) / "new_invalid.py"
        new_file.write_text("""
def foo():
    print('test'
# Missing closing parenthesis - SyntaxError
""")

        # Add to git so it shows in diff
        subprocess.run(
            ["git", "add", "new_invalid.py"],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test", "cwd": self.temp_dir},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        assert result is not None, "Should block when new file has syntax error"
        assert result["decision"] == "block", "Should block the operation"
        assert "new_invalid.py" in result["message"], "Should identify the problematic file"

    # Test 6: No Git Repo - Bash command in non-git directory
    @patch("subprocess.run")
    def test_no_git_repo_uses_fallback(self, mock_subprocess_run):
        """When git is not available, use fallback mtime-based detection."""
        # Mock git to fail (simulating no git available)
        mock_subprocess_run.side_effect = FileNotFoundError("git not found")

        # Create a .py file with syntax error (mixed indentation)
        non_git_dir = tempfile.mkdtemp(prefix="test_no_git_")
        try:
            bad_file = Path(non_git_dir) / "bad.py"
            bad_file.write_text("def foo():\n    print('correct')\n  print('wrong')  # IndentationError\n")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": "echo test", "cwd": non_git_dir},
                "tool_response": {}
            }

            result = check_python_file_edits(data)

            # Should still detect the error via fallback (file was just created)
            assert result is not None, "Should block via fallback detection"
            assert result["decision"] == "block", "Should block the operation"
        finally:
            import shutil
            shutil.rmtree(non_git_dir, ignore_errors=True)

    # Test 7: Virtual Environment - Bash command modifies venv/.py files
    def test_venv_files_skipped(self):
        """When .py files in venv/ are modified, skip validation of venv files."""
        # Create venv directory structure
        venv_dir = Path(self.temp_dir) / ".venv" / "lib" / "python3.12"
        venv_dir.mkdir(parents=True)

        # Create a file in venv with syntax error (should be skipped)
        venv_file = venv_dir / "module.py"
        venv_file.write_text("def foo():\n    print('correct')\n  print('wrong')  # IndentationError\n")

        # Create a file outside venv with syntax error (should be caught)
        bad_file = Path(self.temp_dir) / "bad.py"
        bad_file.write_text("def bar():\n    print('correct')\n  print('wrong')  # IndentationError\n")

        # Add both to git
        subprocess.run(
            ["git", "add", "."],
            cwd=self.temp_dir,
            capture_output=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test", "cwd": self.temp_dir},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        # Should only catch bad.py, not venv files
        assert result is not None, "Should catch non-venv syntax errors"
        assert "bad.py" in result["message"], "Should identify bad.py"
        assert "module.py" not in result["message"], "Should not mention venv files"

    # Test 8: Non-Bash tools - Should return None
    def test_non_bash_tool_returns_none(self):
        """When tool_name is not 'Bash', return None (no validation)."""
        data = {"tool_name": "Write"}

        result = check_python_file_edits(data)

        assert result is None, "Should skip validation for non-Bash tools"

    # Test 9: Empty diff - No files changed
    def test_empty_git_diff_returns_none(self):
        """When git diff returns no changed files, return None."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo no changes"},
            "tool_response": {}
        }

        result = check_python_file_edits(data)

        assert result is None, "Should allow when no .py files changed"


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
