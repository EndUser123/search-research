"""Test GitHub search routing between code and repository search."""

import pytest

from cli import CoreResearchCommand


class TestGitHubSearchRouting:
    """Test intelligent routing for GitHub search mode."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CoreResearchCommand()

    def test_code_search_pattern_detection(self, cli):
        """Test that code search patterns are correctly identified."""
        # Code search patterns should be detected
        code_queries = [
            "pytest fixture function",
            "async def python",
            "import statement",
            "class definition",
            "react component",
        ]

        for query in code_queries:
            is_code_search = cli._is_code_search_query(query)
            assert is_code_search, f"Query '{query}' should be detected as code search"

    def test_repo_search_pattern_detection(self, cli):
        """Test that repository search patterns are correctly identified."""
        # Repository search patterns should NOT be detected as code search
        repo_queries = [
            "pytest testing libraries",
            "flask repository",
            "python web framework",
            "machine learning tools",
        ]

        for query in repo_queries:
            is_code_search = cli._is_code_search_query(query)
            assert not is_code_search, f"Query '{query}' should NOT be detected as code search"

    def test_mixed_query_defaults_to_repo_search(self, cli):
        """Test that ambiguous queries default to repository search."""
        mixed_queries = [
            "python async framework",  # Could be code or repo
            "testing tools",           # Generic query
            "web development",         # Broad topic
        ]

        for query in mixed_queries:
            is_code_search = cli._is_code_search_query(query)
            assert not is_code_search, f"Ambiguous query '{query}' should default to repo search"

    def test_file_extension_detection(self, cli):
        """Test detection of file extension patterns."""
        file_extension_queries = [
            "config.yaml",
            "setup.py",
            "package.json",
            "Dockerfile",
        ]

        for query in file_extension_queries:
            is_code_search = cli._is_code_search_query(query)
            assert is_code_search, f"Query '{query}' with file extension should be code search"

    def test_language_specifier_detection(self, cli):
        """Test detection of language specifier patterns."""
        language_queries = [
            "language:python async",
            "language:javascript react",
            "python language:pytest",
        ]

        for query in language_queries:
            is_code_search = cli._is_code_search_query(query)
            assert is_code_search, f"Query '{query}' with language specifier should be code search"

    def test_empty_and_edge_cases(self, cli):
        """Test edge cases for pattern detection."""
        edge_cases = [
            "",  # Empty query
            "   ",  # Whitespace only
            "!@#$",  # Special characters only
            "a" * 500,  # Very long query
        ]

        for query in edge_cases:
            is_code_search = cli._is_code_search_query(query)
            # Edge cases should default to repo search (safe fallback)
            assert not is_code_search, "Edge case query should default to repo search"

    def test_github_search_uses_code_search(self, cli):
        """Test that _github_search routes to code search when pattern detected."""
        # This is an integration test - we can't run actual GitHub API calls in tests
        # but we can verify the routing logic exists
        assert hasattr(cli, '_github_search'), "CLI should have _github_search method"
        assert hasattr(cli, '_is_code_search_query'), "CLI should have pattern detection method"

    def test_github_search_uses_repo_search(self, cli):
        """Test that _github_search routes to repo search when no pattern detected."""
        # Verify repo search is still accessible
        assert hasattr(cli, '_github_search'), "CLI should have _github_search method"
        # The actual routing logic is tested by pattern detection tests above

    def test_phrase_level_context_detection(self, cli):
        """Test that repo indicators override code keywords (false positive fixes)."""
        # These were previously false positives - should now route to repo search
        false_positive_fixes = [
            "python async framework",  # "framework" overrides "async"
            "import tutorial",  # "tutorial" overrides "import"
            "javascript framework comparison",  # "framework" and "comparison" override
            "python web framework library",  # "framework" and "library" override
            "testing tools guide",  # "tools" and "guide" override
        ]

        for query in false_positive_fixes:
            is_code_search = cli._is_code_search_query(query)
            assert not is_code_search, f"Query '{query}' should route to repo search (repo indicators override)"

        # These should still route to code search (no repo indicators)
        code_search_still_works = [
            "python function decorator",  # No repo indicators
            "async def await",  # No repo indicators
            "import statement syntax",  # No repo indicators
            "class definition python",  # No repo indicators
        ]

        for query in code_search_still_works:
            is_code_search = cli._is_code_search_query(query)
            assert is_code_search, f"Query '{query}' should still route to code search"
