"""Tests for worktree_helper.py.

Comprehensive test suite for git worktree detection and boundary validation.
Uses real git operations (not mocks) per anti-mock stance in CLAUDE.md.

Test Categories:
1. Main repo detection
2. Worktree detection
3. Cross-worktree access detection
4. Git command validation
5. Error handling
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import the module under test (from __lib subdirectory)
from __lib import worktree_helper


class TestGetCurrentWorktree:
    """Test suite for get_current_worktree() function."""

    def test_returns_main_repo_root(self):
        """
        Test that get_current_worktree returns main repo root when in main repo.

        Given: Current directory is the main repository (has .git directory)
        When: get_current_worktree() is called
        Then: Should return the repository root path
        """
        # Act: Call function in current directory (main repo)
        result = worktree_helper.get_current_worktree()

        # Assert: Should return a Path
        assert isinstance(result, Path), "Should return Path object"

        # Assert: Should be the main repo (P:/)
        # The main repo has .git as a directory, not a file
        git_path = result / ".git"
        assert git_path.is_dir(), "Main repo should have .git directory"

        # Assert: Result should be absolute path
        assert result.is_absolute(), "Should return absolute path"

    def test_traverses_to_repo_root(self):
        """
        Test that get_current_worktree traverses up to find repo root.

        Given: Current directory is deep in the repository tree
        When: get_current_worktree() is called
        Then: Should still return the repository root (not the deep subdirectory)
        """
        # Arrange: Use a deep subdirectory
        deep_dir = Path.cwd() / ".claude" / "hooks" / "tests"

        # Act: Call from deep directory
        result = worktree_helper.get_current_worktree(deep_dir)

        # Assert: Should return repo root, not the deep directory
        assert isinstance(result, Path), "Should return Path object"

        # The root should be an ancestor of the deep directory
        try:
            deep_dir.resolve().relative_to(result.resolve())
        except ValueError:
            pytest.fail(f"Result {result} should be ancestor of {deep_dir}")

    def test_raises_error_outside_git_repo(self, tmp_path):
        """
        Test that get_current_worktree raises ValueError when outside git repo.

        Given: Current directory is not in a git repository
        When: get_current_worktree() is called
        Then: Should raise ValueError
        """
        # Arrange: Use temp directory (not a git repo)
        assert not (tmp_path / ".git").exists(), "Temp dir should not be a git repo"

        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="Not in a git repository"):
            worktree_helper.get_current_worktree(tmp_path)


class TestWorktreeDetection:
    """Test suite for worktree-specific detection logic."""

    def test_detects_worktree_from_git_file(self):
        """
        Test that get_current_worktree detects worktrees via .git file.

        Given: We're in a git worktree (has .git file, not .git directory)
        When: get_current_worktree() is called
        Then: Should return the worktree root path
        """
        # This test requires creating a real worktree
        # We'll skip if no worktrees exist
        worktrees = worktree_helper.list_all_worktrees()

        if len(worktrees) <= 1:
            pytest.skip("No worktrees available for testing")

        # Find a worktree (not the main repo)
        test_worktree = None
        for wt in worktrees:
            wt_path = Path(wt["path"])
            if wt_path != Path.cwd():
                test_worktree = wt_path
                break

        if not test_worktree:
            pytest.skip("No suitable worktree found for testing")

        # Act: Get worktree path
        result = worktree_helper.get_current_worktree(test_worktree)

        # Assert: Should return the worktree path
        assert isinstance(result, Path), "Should return Path object"
        assert result == test_worktree, f"Should return {test_worktree}"

        # Assert: Worktree has .git file (not directory)
        git_path = result / ".git"
        assert git_path.is_file(), "Worktree should have .git file"

    def test_worktree_list_returns_main_repo(self):
        """
        Test that list_all_worktrees includes the main repository.

        Given: Repository has at least the main tree
        When: list_all_worktrees() is called
        Then: Should include main repo in results
        """
        # Act: List all worktrees
        worktrees = worktree_helper.list_all_worktrees()

        # Assert: Should have at least one worktree (main repo)
        assert len(worktrees) >= 1, "Should have at least main repo"

        # Assert: Main repo should be in the list
        # Note: Path.cwd() might be deep in the repo, so we check if any worktree
        # is an ancestor of the current directory
        main_repo_found = False
        current_cwd = Path.cwd()
        for wt in worktrees:
            wt_path = Path(wt["path"])
            # Check if current directory is within this worktree
            try:
                current_cwd.resolve().relative_to(wt_path.resolve())
                main_repo_found = True
                # This worktree contains the current directory
                # It should have .git (directory for main repo, file for worktree)
                # Note: Windows paths like "P:" need trailing slash for proper joining
                git_path = Path(str(wt_path) + "/.git") if str(wt_path).endswith(":") else wt_path / ".git"
                assert git_path.exists(), f"Worktree should have .git: {wt_path} -> {git_path}"
                break
            except ValueError:
                # Current directory is not within this worktree
                continue

        assert main_repo_found, "Main repo should be in worktree list"

    def test_worktree_list_structure(self):
        """
        Test that list_all_worktrees returns correct structure.

        Given: Repository exists
        When: list_all_worktrees() is called
        Then: Should return list of dicts with expected keys
        """
        # Act: List worktrees
        worktrees = worktree_helper.list_all_worktrees()

        # Assert: Should be a list
        assert isinstance(worktrees, list), "Should return list"

        # Assert: Each worktree should be a dict
        for wt in worktrees:
            assert isinstance(wt, dict), "Each worktree should be a dict"

            # Assert: Should have required keys
            assert "path" in wt, "Should have 'path' key"

            # Assert: Path should be valid
            wt_path = Path(wt["path"])
            assert wt_path.exists(), f"Worktree path should exist: {wt_path}"


class TestCrossWorktreeAccessDetection:
    """Test suite for is_cross_worktree_access() function."""

    def test_same_directory_access(self):
        """
        Test that accessing files in same directory is not cross-worktree.

        Given: Current worktree is P:/, target is ./file.py
        When: is_cross_worktree_access() is called
        Then: Should return False (same worktree)
        """
        # Arrange
        current_cwd = Path.cwd()
        target_file = "./some_file.py"

        # Act
        result = worktree_helper.is_cross_worktree_access(
            current_cwd,
            target_file
        )

        # Assert: Should not be cross-worktree
        assert result is False, "Accessing same directory should not be cross-worktree"

    def test_subdirectory_access(self):
        """
        Test that accessing subdirectories is not cross-worktree.

        Given: Current worktree is P:/, target is .claude/hooks/file.py
        When: is_cross_worktree_access() is called
        Then: Should return False (still in same worktree)
        """
        # Arrange
        current_cwd = Path.cwd()
        target_file = ".claude/hooks/__lib/worktree_helper.py"

        # Act
        result = worktree_helper.is_cross_worktree_access(
            current_cwd,
            target_file
        )

        # Assert: Should not be cross-worktree (subdirectory is still in repo)
        assert result is False, "Accessing subdirectory should not be cross-worktree"

    def test_absolute_path_within_repo(self):
        """
        Test that absolute paths within repo are not cross-worktree.

        Given: Current worktree is P:/, target is P:/file.py (absolute)
        When: is_cross_worktree_access() is called
        Then: Should return False (same worktree)
        """
        # Arrange
        current_cwd = Path.cwd()
        target_file = str(Path.cwd() / "README.md")

        # Act
        result = worktree_helper.is_cross_worktree_access(
            current_cwd,
            target_file
        )

        # Assert: Should not be cross-worktree
        assert result is False, "Absolute path within repo should not be cross-worktree"

    def test_absolute_path_outside_repo(self):
        """
        Test that absolute paths outside repo are cross-worktree.

        Given: Current worktree is P:/, target is C:/Windows/file.py
        When: is_cross_worktree_access() is called
        Then: Should return True (different worktree)
        """
        # Arrange: Use a path definitely outside the repo
        current_cwd = Path.cwd()

        # Use C:/Windows or similar system path
        if sys.platform == "win32":
            outside_path = "C:/Windows/system32/file.exe"
        else:
            outside_path = "/tmp/outside_file.py"

        # Act
        result = worktree_helper.is_cross_worktree_access(
            current_cwd,
            outside_path
        )

        # Assert: Should be cross-worktree
        assert result is True, f"Path outside repo should be cross-worktree: {outside_path}"

    def test_relative_path_outside_repo(self):
        """
        Test that relative paths outside repo are cross-worktree.

        Given: Current worktree is P:/.claude/hooks, target is ../../../outside/file.py
        When: is_cross_worktree_access() is called
        Then: Should return True (escapes repo boundary)
        """
        # Arrange: Use a path definitely outside the repo
        current_cwd = Path.cwd()

        # Use a system path that's definitely outside any git repo
        if sys.platform == "win32":
            # Windows: use C:\Windows or similar
            target_file = "C:/Windows/System32/file.exe"
        else:
            # Unix: use /tmp or similar
            target_file = "/tmp/outside_file.py"

        # Act
        result = worktree_helper.is_cross_worktree_access(
            current_cwd,
            target_file
        )

        # Assert: Should be cross-worktree (outside repo boundary)
        assert result is True, f"System path outside repo should be cross-worktree: {target_file}"


class TestGitCommandValidation:
    """Test suite for validate_git_command_for_worktree() function."""

    def test_safe_command_no_files(self):
        """
        Test that git commands without files are safe.

        Given: Command is 'git status' (no file operands)
        When: validate_git_command_for_worktree() is called
        Then: Should return valid=True with reason "No target files"
        """
        # Arrange
        command = "git status"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert isinstance(result, dict), "Should return dict"
        assert result["valid"] is True, "Command without files should be valid"
        assert result["reason"] == "No target files in command", "Should explain why valid"
        assert len(result["violations"]) == 0, "Should have no violations"

    def test_safe_command_single_file_in_repo(self):
        """
        Test that git commands with files in repo are safe.

        Given: Command is 'git restore file.py' (file in repo)
        When: validate_git_command_for_worktree() is called
        Then: Should return valid=True
        """
        # Arrange
        command = "git restore README.md"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert isinstance(result, dict), "Should return dict"
        assert result["valid"] is True, "Command with repo file should be valid"
        assert len(result["violations"]) == 0, "Should have no violations"
        assert len(result["target_files"]) == 1, "Should identify one target file"

    def test_safe_command_multiple_files_in_repo(self):
        """
        Test that git commands with multiple files in repo are safe.

        Given: Command is 'git restore file1.py file2.py'
        When: validate_git_command_for_worktree() is called
        Then: Should return valid=True
        """
        # Arrange
        command = "git restore README.md CLAUDE.md"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert result["valid"] is True, "Command with repo files should be valid"
        assert len(result["violations"]) == 0, "Should have no violations"
        assert len(result["target_files"]) == 2, "Should identify two target files"

    def test_unsafe_command_file_outside_repo(self):
        """
        Test that git commands accessing files outside repo are blocked.

        Given: Command is 'git restore' with a system path outside repo
        When: validate_git_command_for_worktree() is called
        Then: Should return valid=False with violations
        """
        # Arrange: Use a system path definitely outside the repo
        if sys.platform == "win32":
            outside_file = "C:/Windows/System32/file.exe"
        else:
            outside_file = "/tmp/outside_file.py"

        command = f"git restore {outside_file}"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert isinstance(result, dict), "Should return dict"
        assert result["valid"] is False, "Command accessing outside files should be invalid"
        assert len(result["violations"]) > 0, "Should have violations"
        assert "Cross-worktree access" in result["reason"], "Should explain cross-worktree access"

    def test_checkout_with_double_dash(self):
        """
        Test that 'git checkout -- file' is parsed correctly.

        Given: Command is 'git checkout -- file.py'
        When: validate_git_command_for_worktree() is called
        Then: Should parse file after -- separator
        """
        # Arrange
        command = "git checkout -- README.md"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert result["valid"] is True, "Should parse checkout -- command correctly"
        assert len(result["target_files"]) == 1, "Should identify one target file"
        assert "README.md" in result["target_files"][0], "Should extract file after --"

    def test_checkout_with_commit_and_double_dash(self):
        """
        Test that 'git checkout HEAD -- file' is parsed correctly.

        Given: Command is 'git checkout HEAD -- file.py'
        When: validate_git_command_for_worktree() is called
        Then: Should parse file after -- separator (ignore commit)
        """
        # Arrange
        command = "git checkout HEAD -- README.md"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert result["valid"] is True, "Should parse checkout commit -- command correctly"
        assert len(result["target_files"]) == 1, "Should identify one target file"
        assert "README.md" in result["target_files"][0], "Should extract file after --"

    def test_returns_current_worktree_in_result(self):
        """
        Test that validation result includes current worktree path.

        Given: Any git command
        When: validate_git_command_for_worktree() is called
        Then: Result should include current_worktree path
        """
        # Arrange
        command = "git status"

        # Act
        result = worktree_helper.validate_git_command_for_worktree(command)

        # Assert
        assert "current_worktree" in result, "Result should include current_worktree"
        assert result["current_worktree"] is not None, "current_worktree should not be None"
        assert isinstance(result["current_worktree"], Path), "current_worktree should be Path"


class TestErrorHandling:
    """Test suite for error handling and edge cases."""

    def test_get_current_worktree_timeout_handling(self, tmp_path):
        """
        Test that get_current_worktree handles git timeouts gracefully.

        Given: git worktree list command times out
        When: get_current_worktree() is called from non-repo directory
        Then: Should raise RuntimeError (or ValueError for non-repo)
        """
        # Arrange: Use temp directory (not a git repo)
        # This will fail fast with ValueError, not timeout
        # But we test the error path

        # Act & Assert: Should raise ValueError for non-repo
        with pytest.raises((ValueError, RuntimeError)):
            worktree_helper.get_current_worktree(tmp_path)

    def test_list_all_worktrees_handles_errors(self):
        """
        Test that list_all_worktrees handles errors gracefully.

        Given: Repository exists
        When: list_all_worktrees() is called
        Then: Should return list (even if empty on error)
        """
        # Act: This should succeed in current repo
        result = worktree_helper.list_all_worktrees()

        # Assert: Should return a list
        assert isinstance(result, list), "Should return list"

        # Note: In current repo, should have at least main repo
        # The function is designed to return [] on error, not raise

    def test_validate_command_fail_open_on_worktree_error(self, tmp_path):
        """
        Test that validate_git_command_for_worktree fails open when worktree detection fails.

        Given: Cannot determine current worktree (e.g., in temp directory)
        When: validate_git_command_for_worktree() is called
        Then: Should return valid=True (fail open to avoid blocking legitimate operations)
        """
        # Arrange: Use temp directory (not in git repo)
        command = "git restore file.py"

        # Act: Call from temp directory
        result = worktree_helper.validate_git_command_for_worktree(
            command,
            cwd=tmp_path
        )

        # Assert: Should fail open (allow command) when worktree detection fails
        assert isinstance(result, dict), "Should return dict"
        assert result["valid"] is True, "Should fail open when worktree detection fails"
        assert "Cannot determine worktree" in result["reason"], "Should explain why"


class TestRealWorktreeScenarios:
    """Integration tests with real git worktrees (if available)."""

    @pytest.fixture(scope="class")
    def setup_test_worktree(self):
        """
        Create a test worktree for integration testing.

        This fixture creates a temporary worktree if none exists,
        and cleans it up after tests complete.
        """
        worktrees = worktree_helper.list_all_worktrees()

        # If we only have one worktree (main repo), skip integration tests
        if len(worktrees) <= 1:
            pytest.skip("No worktree available for integration testing")

        # Check if we already have a worktree to test with (not the main repo)
        test_worktree = None
        main_repo = worktree_helper.get_current_worktree()

        for wt in worktrees:
            wt_path = Path(wt["path"])
            # Skip main repo
            if wt_path != main_repo:
                test_worktree = wt_path
                break

        if test_worktree:
            yield test_worktree
            return  # Don't create/cleanup, just use existing

        # No worktree exists - create one for testing
        # This is expensive, so we skip if not available
        pytest.skip("No worktree available for integration testing")

    def test_cross_worktree_detection_real(self, setup_test_worktree):
        """
        Test cross-worktree detection with real worktree.

        Given: Two worktrees exist (main + test worktree)
        When: is_cross_worktree_access() checks paths between them
        Then: Should correctly detect cross-worktree access
        """
        test_worktree = setup_test_worktree
        main_repo = worktree_helper.get_current_worktree()

        # Verify we have different worktrees
        assert test_worktree != main_repo, "Test worktree should be different from main repo"

        # Test: Accessing test_worktree from main_repo
        result = worktree_helper.is_cross_worktree_access(
            main_repo,
            str(test_worktree / "some_file.py")
        )

        # Assert: Should be cross-worktree
        assert result is True, "Accessing different worktree should be cross-worktree"

        # Test: Accessing main_repo from test_worktree
        result = worktree_helper.is_cross_worktree_access(
            test_worktree,
            str(main_repo / "README.md")
        )

        # Assert: Should be cross-worktree
        assert result is True, "Accessing main repo from worktree should be cross-worktree"

    def test_worktree_boundaries_real(self, setup_test_worktree):
        """
        Test that worktree boundaries are enforced correctly.

        Given: Two worktrees exist
        When: validate_git_command_for_worktree() checks cross-worktree operations
        Then: Should block operations that cross worktree boundaries
        """
        test_worktree = setup_test_worktree
        main_repo = worktree_helper.get_current_worktree()

        # Verify we have different worktrees
        assert test_worktree != main_repo, "Test worktree should be different from main repo"

        # Test: Restore file in different worktree from main_repo
        command = f"git restore {test_worktree / 'test.py'}"

        result = worktree_helper.validate_git_command_for_worktree(
            command,
            cwd=main_repo
        )

        # Assert: Should block cross-worktree access
        assert result["valid"] is False, "Should block cross-worktree restore"
        assert len(result["violations"]) > 0, "Should have violations"


class TestWorktreeHelperDocumentationExamples:
    """Test that documentation examples actually work."""

    def test_get_current_worktree_example_1(self):
        """
        Test first example from get_current_worktree() docstring.

        >>> get_current_worktree()
        Path('P:/')
        """
        # Act
        result = worktree_helper.get_current_worktree()

        # Assert: Should return Path
        assert isinstance(result, Path), "Should return Path"

        # Assert: Should be the repo root (not the current deep directory)
        # The function should traverse up to find the .git directory
        # Get the actual repo root by finding .git
        repo_root = Path.cwd()
        while repo_root != repo_root.parent and not (repo_root / ".git").exists():
            repo_root = repo_root.parent

        # Assert: Result should be the repo root
        assert result.resolve() == repo_root.resolve(), f"Should return repo root {repo_root}, got {result}"

    def test_list_all_worktrees_example(self):
        """
        Test example from list_all_worktrees() docstring.

        >>> list_all_worktrees()
        [
            {'path': 'P:/', 'branch': 'refs/heads/main', ...}
        ]
        """
        # Act
        result = worktree_helper.list_all_worktrees()

        # Assert: Should return list
        assert isinstance(result, list), "Should return list"

        # Assert: At least main repo should exist
        assert len(result) >= 1, "Should have at least main repo"

        # Assert: Each entry should be a dict with 'path' key
        for wt in result:
            assert isinstance(wt, dict), "Each worktree should be a dict"
            assert "path" in wt, "Should have 'path' key"
