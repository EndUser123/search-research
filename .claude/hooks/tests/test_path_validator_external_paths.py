"""Tests for DirectoryPolicy.get_allowed_external_paths() method."""

import os
import sys

# Add hooks directory to path for imports
hooks_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hooks_dir not in sys.path:
    sys.path.insert(0, hooks_dir)

from __lib.path_validator import DirectoryPolicy


class TestGetAllowedExternalPaths:
    """Tests for get_allowed_external_paths method."""

    def test_returns_dict_with_patterns_and_exact_paths_keys(self):
        """Test that result has expected keys."""
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "exact_paths" in result

    def test_patterns_is_list_of_strings(self):
        """Test that patterns is a list of strings."""
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        assert isinstance(result["patterns"], list)
        for pattern in result["patterns"]:
            assert isinstance(pattern, str)

    def test_exact_paths_is_list_of_strings(self):
        """Test that exact_paths is a list of strings."""
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        assert isinstance(result["exact_paths"], list)
        for path in result["exact_paths"]:
            assert isinstance(path, str)

    def test_exact_paths_contains_auto_memory_directory(self):
        """
        Test that exact_paths contains the auto memory directory.

        This path was previously in the hardcoded ALLOWED_EXTERNAL_PATHS
        constant and should now be in directory_policy.json.
        """
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        expected = "C:/Users/brsth/.claude/projects/"
        assert expected in result["exact_paths"], \
            f"Expected '{expected}' in exact_paths. Got: {result['exact_paths']}"

    def test_exact_paths_contains_gemini_brain_directory(self):
        """
        Test that exact_paths contains the gemini brain directory.

        This path was previously in the hardcoded ALLOWED_EXTERNAL_PATHS
        constant and should now be in directory_policy.json.
        """
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        expected = "C:/Users/brsth/.gemini/antigravity/brain/"
        assert expected in result["exact_paths"], \
            f"Expected '{expected}' in exact_paths. Got: {result['exact_paths']}"

    def test_patterns_contains_site_packages_patterns(self):
        """Test that patterns contains site-packages wildcard patterns."""
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        # Should contain site-packages patterns
        patterns_str = " ".join(result["patterns"])
        assert "site-packages" in patterns_str, \
            f"Expected site-packages patterns. Got: {result['patterns']}"

    def test_patterns_contains_claude_plans_patterns(self):
        """Test that patterns contains .claude/plans wildcard patterns."""
        policy = DirectoryPolicy()
        result = policy.get_allowed_external_paths()

        # Should contain .claude/plans patterns
        patterns_str = " ".join(result["patterns"])
        assert ".claude/plans" in patterns_str, \
            f"Expected .claude/plans patterns. Got: {result['patterns']}"
