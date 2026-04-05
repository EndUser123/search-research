"""
Tests for commit message parser utilities.

These tests verify git diff parsing and commit message generation
functionality for intelligent commit message creation.

Test coverage:
- Git diff output parsing into structured data
- File type detection (.py, .md, etc.)
- Scope detection (hooks, skills, commands, etc.)
- Commit type generation (feat, fix, docs, etc.)
- Meaningful subject line generation
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestGitDiffParsing:
    """Test parsing git diff output into structured data."""

    def test_parse_simple_file_diff(self):
        """
        Test parsing a simple single-file diff.

        Given: A git diff output for a single Python file
        When: The diff is parsed
        Then: Should return structured data with file path and line changes
        """
        # Sample git diff output
        diff_output = """diff --git a/src/example.py b/src/example.py
index 1234567..abcdefg 100644
--- a/src/example.py
+++ b/src/example.py
@@ -1,5 +1,7 @@
 def hello():
-    print("old")
+    print("new")
     return True
+    print("added")
"""

        # This should fail because the module doesn't exist yet
        from commit_message_parser import parse_git_diff

        result = parse_git_diff(diff_output)

        assert result is not None
        assert "files" in result
        assert len(result["files"]) == 1
        assert result["files"][0]["path"] == "src/example.py"
        assert result["files"][0]["additions"] == 2
        assert result["files"][0]["deletions"] == 1

    def test_parse_multi_file_diff(self):
        """
        Test parsing a diff with multiple files.

        Given: A git diff output with multiple changed files
        When: The diff is parsed
        Then: Should return structured data for all files
        """
        diff_output = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
 def main():
+    print("new line")
     pass
diff --git a/README.md b/README.md
index abcdefg..1234567 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Project
+New section
"""

        from commit_message_parser import parse_git_diff

        result = parse_git_diff(diff_output)

        assert len(result["files"]) == 2
        assert any(f["path"] == "src/main.py" for f in result["files"])
        assert any(f["path"] == "README.md" for f in result["files"])

    def test_parse_binary_file_diff(self):
        """
        Test parsing a diff that includes binary files.

        Given: A git diff output with binary file changes
        When: The diff is parsed
        Then: Should mark binary files appropriately
        """
        diff_output = """diff --git a/image.png b/image.png
index 1234567..abcdefg 100644
Binary files a/image.png and b/image.png differ
"""

        from commit_message_parser import parse_git_diff

        result = parse_git_diff(diff_output)

        assert len(result["files"]) == 1
        assert result["files"][0]["binary"] is True


class TestFileTypeDetection:
    """Test file type detection from file paths."""

    def test_detect_python_file_type(self):
        """
        Test detecting Python files.

        Given: A file path ending in .py
        When: File type is detected
        Then: Should return 'python'
        """
        from commit_message_parser import detect_file_type

        result = detect_file_type("src/module.py")
        assert result == "python"

    def test_detect_markdown_file_type(self):
        """
        Test detecting Markdown files.

        Given: A file path ending in .md
        When: File type is detected
        Then: Should return 'markdown'
        """
        from commit_message_parser import detect_file_type

        result = detect_file_type("docs/README.md")
        assert result == "markdown"

    def test_detect_yaml_file_type(self):
        """
        Test detecting YAML files.

        Given: A file path ending in .yaml or .yml
        When: File type is detected
        Then: Should return 'yaml'
        """
        from commit_message_parser import detect_file_type

        result1 = detect_file_type("config.yaml")
        result2 = detect_file_type("config.yml")
        assert result1 == "yaml"
        assert result2 == "yaml"

    def test_detect_json_file_type(self):
        """
        Test detecting JSON files.

        Given: A file path ending in .json
        When: File type is detected
        Then: Should return 'json'
        """
        from commit_message_parser import detect_file_type

        result = detect_file_type("settings.json")
        assert result == "json"

    def test_detect_unknown_file_type(self):
        """
        Test detecting unknown file types.

        Given: A file path with unknown extension
        When: File type is detected
        Then: Should return 'unknown'
        """
        from commit_message_parser import detect_file_type

        result = detect_file_type("file.unknown")
        assert result == "unknown"


class TestScopeDetection:
    """Test scope detection from file paths and changes."""

    def test_detect_hooks_scope(self):
        """
        Test detecting hooks scope from .claude/hooks/ paths.

        Given: File paths in .claude/hooks/
        When: Scope is detected
        Then: Should include 'hooks' in the detected scopes
        """
        from commit_message_parser import detect_scope

        files = [
            ".claude/hooks/PreToolUse_gate.py",
            ".claude/hooks/PostToolUse_logger.py",
        ]

        result = detect_scope(files)
        assert "hooks" in result

    def test_detect_skills_scope(self):
        """
        Test detecting skills scope from .claude/skills/ paths.

        Given: File paths in .claude/skills/
        When: Scope is detected
        Then: Should include 'skills' in the detected scopes
        """
        from commit_message_parser import detect_scope

        files = [
            ".claude/skills/tdd/SKILL.md",
            ".claude/skills/rca/SKILL.md",
        ]

        result = detect_scope(files)
        assert "skills" in result

    def test_detect_commands_scope(self):
        """
        Test detecting commands scope from command paths.

        Given: File paths indicating command changes
        When: Scope is detected
        Then: Should include 'commands' in the detected scopes
        """
        from commit_message_parser import detect_scope

        files = [
            "src/commands/my_command.py",
            "__csf/src/commands/management/sap_commit.py",
        ]

        result = detect_scope(files)
        assert "commands" in result

    def test_detect_tests_scope(self):
        """
        Test detecting tests scope from test file paths.

        Given: File paths in tests/ directories
        When: Scope is detected
        Then: Should include 'tests' in the detected scopes
        """
        from commit_message_parser import detect_scope

        files = [
            "tests/test_feature.py",
            ".claude/hooks/tests/test_hook.py",
        ]

        result = detect_scope(files)
        assert "tests" in result

    def test_detect_docs_scope(self):
        """
        Test detecting docs scope from documentation paths.

        Given: File paths in docs/ directories
        When: Scope is detected
        Then: Should include 'docs' in the detected scopes
        """
        from commit_message_parser import detect_scope

        files = [
            "docs/README.md",
            ".claude/docs/ARCHITECTURE.md",
        ]

        result = detect_scope(files)
        assert "docs" in result

    def test_detect_multiple_scopes(self):
        """
        Test detecting multiple scopes from mixed file paths.

        Given: File paths from different areas
        When: Scope is detected
        Then: Should return all relevant scopes
        """
        from commit_message_parser import detect_scope

        files = [
            ".claude/hooks/PreToolUse_gate.py",
            ".claude/skills/tdd/SKILL.md",
            "docs/README.md",
        ]

        result = detect_scope(files)
        assert "hooks" in result
        assert "skills" in result
        assert "docs" in result

    def test_empty_files_returns_no_scope(self):
        """
        Test scope detection with no files.

        Given: An empty file list
        When: Scope is detected
        Then: Should return empty list
        """
        from commit_message_parser import detect_scope

        result = detect_scope([])
        assert result == []


class TestCommitTypeDetection:
    """Test commit type detection from changes."""

    def test_new_file_returns_feat_type(self):
        """
        Test that new files result in 'feat' type.

        Given: A diff showing a new file
        When: Commit type is detected
        Then: Should return 'feat'
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "src/new_feature.py", "new": True}
            ]
        }

        result = detect_commit_type(diff_data)
        assert result == "feat"

    def test_deleted_file_returns_fix_type(self):
        """
        Test that deleted files result in 'fix' type.

        Given: A diff showing a deleted file
        When: Commit type is detected
        Then: Should return 'fix' (cleanup/removal)
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "src/old_feature.py", "deleted": True}
            ]
        }

        result = detect_commit_type(diff_data)
        assert result in ["fix", "refactor"]

    def test_doc_changes_return_docs_type(self):
        """
        Test that documentation changes result in 'docs' type.

        Given: A diff showing only documentation changes
        When: Commit type is detected
        Then: Should return 'docs'
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "README.md", "type": "markdown"},
                {"path": "docs/GUIDE.md", "type": "markdown"},
            ]
        }

        result = detect_commit_type(diff_data)
        assert result == "docs"

    def test_test_changes_return_test_type(self):
        """
        Test that test file changes result in 'test' type.

        Given: A diff showing only test file changes
        When: Commit type is detected
        Then: Should return 'test'
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "tests/test_feature.py", "type": "python"},
                {"path": ".claude/hooks/tests/test_hook.py", "type": "python"},
            ]
        }

        result = detect_commit_type(diff_data)
        assert result == "test"

    def test_config_changes_return_chore_type(self):
        """
        Test that configuration changes result in 'chore' type.

        Given: A diff showing only configuration file changes
        When: Commit type is detected
        Then: Should return 'chore'
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "settings.json", "type": "json"},
                {"path": "config.yaml", "type": "yaml"},
            ]
        }

        result = detect_commit_type(diff_data)
        assert result == "chore"

    def test_mixed_changes_prioritize_feature_type(self):
        """
        Test commit type with mixed file changes.

        Given: A diff showing both feature and documentation changes
        When: Commit type is detected
        Then: Should prioritize 'feat' over 'docs'
        """
        from commit_message_parser import detect_commit_type

        diff_data = {
            "files": [
                {"path": "src/feature.py", "type": "python", "new": True},
                {"path": "README.md", "type": "markdown"},
            ]
        }

        result = detect_commit_type(diff_data)
        assert result == "feat"


class TestSubjectGeneration:
    """Test subject line generation from parsed diff data."""

    def test_subject_for_python_file_additions(self):
        """
        Test generating subject for Python file additions.

        Given: A diff adding Python code
        When: Subject line is generated
        Then: Should describe the Python changes meaningfully
        """
        from commit_message_parser import generate_subject

        diff_data = {
            "files": [
                {"path": "src/auth.py", "type": "python", "additions": 15, "deletions": 0}
            ],
            "scopes": ["auth"]
        }

        result = generate_subject(diff_data)
        assert result is not None
        assert len(result) > 0
        assert len(result) <= 72  # Conventional commits soft limit
        # Should be lowercase
        assert result == result.lower()

    def test_subject_for_hook_modifications(self):
        """
        Test generating subject for hook modifications.

        Given: A diff modifying hook files
        When: Subject line is generated
        Then: Should mention hooks in the subject
        """
        from commit_message_parser import generate_subject

        diff_data = {
            "files": [
                {"path": ".claude/hooks/PreToolUse_gate.py", "additions": 5, "deletions": 2}
            ],
            "scopes": ["hooks"]
        }

        result = generate_subject(diff_data)
        assert result is not None
        # Should reference hooks or the specific hook
        assert "hook" in result or "gate" in result or "pretooluse" in result

    def test_subject_for_doc_updates(self):
        """
        Test generating subject for documentation updates.

        Given: A diff updating documentation
        When: Subject line is generated
        Then: Should describe documentation changes
        """
        from commit_message_parser import generate_subject

        diff_data = {
            "files": [
                {"path": "README.md", "type": "markdown", "additions": 10, "deletions": 5}
            ],
            "scopes": ["docs"]
        }

        result = generate_subject(diff_data)
        assert result is not None
        assert "update" in result or "document" in result or "readme" in result

    def test_subject_no_period(self):
        """
        Test that generated subjects don't end with period.

        Given: Any diff data
        When: Subject line is generated
        Then: Should not end with a period
        """
        from commit_message_parser import generate_subject

        diff_data = {
            "files": [
                {"path": "src/test.py", "type": "python", "additions": 1}
            ],
            "scopes": []
        }

        result = generate_subject(diff_data)
        assert not result.endswith(".")


class TestFullCommitMessageGeneration:
    """Test complete commit message generation. """

    def test_generate_full_commit_message(self):
        """
        Test generating a complete commit message.

        Given: Parsed git diff data
        When: Full commit message is generated
        Then: Should include type, scope, and subject in proper format
        """
        from commit_message_parser import generate_commit_message

        diff_data = {
            "files": [
                {"path": ".claude/hooks/new_hook.py", "type": "python", "new": True, "additions": 50}
            ],
            "scopes": ["hooks"],
            "type": "feat"
        }

        result = generate_commit_message(diff_data)

        # Check conventional commits format
        assert ":" in result
        parts = result.split(":", 1)
        assert len(parts) == 2

        commit_type, rest = parts
        assert commit_type in ["feat", "fix", "docs", "test", "chore", "refactor"]
        assert rest.strip()  # Subject should not be empty

    def test_generate_commit_message_with_scope(self):
        """
        Test generating commit message with explicit scope.

        Given: Diff data with detected scope
        When: Commit message is generated
        Then: Should include scope in parentheses
        """
        from commit_message_parser import generate_commit_message

        diff_data = {
            "files": [
                {"path": ".claude/hooks/test.py", "type": "python"}
            ],
            "scopes": ["hooks"],
            "type": "fix"
        }

        result = generate_commit_message(diff_data)
        # Should match format: type(scope): subject
        assert "(" in result and ")" in result

    def test_generate_commit_message_multiple_files(self):
        """
        Test generating commit message for multiple files.

        Given: Diff data with multiple changed files
        When: Commit message is generated
        Then: Should reflect the primary change type
        """
        from commit_message_parser import generate_commit_message

        diff_data = {
            "files": [
                {"path": "src/feature.py", "type": "python", "new": True},
                {"path": "tests/test_feature.py", "type": "python", "new": True},
            ],
            "scopes": ["feature", "tests"],
            "type": "feat"
        }

        result = generate_commit_message(diff_data)
        assert result.startswith("feat")
        assert ":" in result


class TestIntegrationWithGit:
    """Integration tests with actual git commands (mocked)."""

    def test_parse_git_staged_diff(self):
        """
        Test parsing diff from git diff --staged output.

        Given: A mock git repository with staged changes
        When: Git diff output is parsed
        Then: Should return structured commit data
        """
        mock_diff_output = """diff --git a/src/example.py b/src/example.py
index 1234567..abcdefg 100644
--- a/src/example.py
+++ b/src/example.py
@@ -1,3 +1,4 @@
 def test():
+    new_line()
     pass
"""

        from commit_message_parser import parse_staged_changes

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_diff_output, returncode=0)

            result = parse_staged_changes(repo_path=".")

            assert result is not None
            assert "files" in result

    @pytest.fixture
    def sample_diff_data(self):
        """Sample structured diff data for testing."""
        return {
            "files": [
                {
                    "path": ".claude/hooks/test_hook.py",
                    "type": "python",
                    "additions": 10,
                    "deletions": 2
                }
            ],
            "scopes": ["hooks"],
            "type": "feat"
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
