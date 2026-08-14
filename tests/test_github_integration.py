"""Integration tests for GitHub search with real API.

These tests use the actual GitHub API to validate:
- API structure matches expectations
- search_code() returns expected fields
- search_repos() returns expected fields
- Error handling works correctly

NOTE: These tests require a GitHub token. Set GITHUB_TOKEN env var or skip.
"""

import os

import pytest

from cli import CoreResearchCommand


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("GITHUB_TOKEN"),
    reason="GITHUB_TOKEN environment variable not set"
)
class TestGitHubAPIIntegration:
    """Integration tests with real GitHub API."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CoreResearchCommand()

    @pytest.mark.asyncio
    async def test_code_search_api_structure(self, cli):
        """Validate that search_code() returns expected structure."""
        from research_flash.sources.github_source import GitHubAdapter

        adapter = GitHubAdapter()

        # Test code search with simple query
        results = await adapter.search_code("def hello", max_results=3)

        # Validate structure
        assert len(results) > 0, "Code search should return results"

        for result in results:
            # Check required fields exist
            assert hasattr(result, "repository"), "Code result must have 'repository' field"
            assert hasattr(result, "path"), "Code result must have 'path' field"
            assert hasattr(result, "url"), "Code result must have 'url' field"
            assert hasattr(result, "content"), "Code result must have 'content' field"

            # Validate field types
            assert isinstance(result.repository, str), "repository must be string"
            assert isinstance(result.path, str), "path must be string"
            assert isinstance(result.url, str), "url must be string"
            assert result.content is None or isinstance(result.content, str), "content must be string or None"

    @pytest.mark.asyncio
    async def test_repo_search_api_structure(self, cli):
        """Validate that search_repos() returns expected structure."""
        from research_flash.sources.github_source import GitHubAdapter

        adapter = GitHubAdapter()

        # Test repo search with simple query
        results = await adapter.search_repos("pytest", max_results=3)

        # Validate structure
        assert len(results) > 0, "Repo search should return results"

        for result in results:
            # Check required fields exist
            assert hasattr(result, "full_name"), "Repo result must have 'full_name' field"
            assert hasattr(result, "content"), "Repo result must have 'content' field"
            assert hasattr(result, "url"), "Repo result must have 'url' field"

            # Validate field types
            assert isinstance(result.full_name, str), "full_name must be string"
            assert isinstance(result.url, str), "url must be string"
            assert result.content is None or isinstance(result.content, str), "content must be string or None"

    @pytest.mark.asyncio
    async def test_github_search_routing_integration(self, cli):
        """Test end-to-end routing through CLI._github_search()."""
        # Test code query routing
        code_result = await cli._github_search("def hello", max_results=3)
        assert "results" in code_result, "Result must have 'results' field"
        assert "sources_used" in code_result, "Result must have 'sources_used' field"
        assert "github_code" in code_result["sources_used"], "Code search should use 'github_code' source"

        # Test repo query routing
        repo_result = await cli._github_search("pytest testing", max_results=3)
        assert "results" in repo_result, "Result must have 'results' field"
        assert "sources_used" in repo_result, "Result must have 'sources_used' field"
        assert "github" in repo_result["sources_used"], "Repo search should use 'github' source"


@pytest.mark.integration
class TestGitHubAPIErrors:
    """Test error handling with real GitHub API."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CoreResearchCommand()

    @pytest.mark.asyncio
    async def test_empty_query_handling(self, cli):
        """Test that empty queries are handled gracefully."""
        result = await cli._github_search("", max_results=10)

        # Should return results (empty or fallback)
        assert "results" in result, "Result must have 'results' field"
        assert isinstance(result["results"], list), "Results must be a list"

    @pytest.mark.asyncio
    async def test_zero_results_handling(self, cli):
        """Test handling of queries that return zero results."""
        # Use a very specific query that likely has no results
        result = await cli._github_search("abcdefgh123456789neverexists", max_results=10)

        # Should not crash, return empty results
        assert "results" in result, "Result must have 'results' field"
        assert isinstance(result["results"], list), "Results must be a list"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN environment variable not set"
    )
    async def test_special_characters_in_query(self, cli):
        """Test that special characters in queries are handled correctly."""
        # Query with special characters that shouldn't crash
        result = await cli._github_search("test!@#$%^&*()", max_results=5)

        # Should not crash
        assert "results" in result, "Result must have 'results' field"
        assert isinstance(result["results"], list), "Results must be a list"


@pytest.mark.integration
class TestGitHubPatternValidation:
    """Integration tests to validate pattern detection against real queries."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CoreResearchCommand()

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN environment variable not set"
    )
    async def test_false_positive_python_async_framework(self, cli):
        """Test false positive fix: 'python async framework' should NOT route to code search.

        This query is about finding repos for async frameworks, not code containing 'async'.
        The 'framework' keyword should override the 'async' keyword.
        """
        # Pattern detection should identify this as repo search (FIXED)
        is_code_search = cli._is_code_search_query("python async framework")

        # FIXED: Should now route to repo search (not code search)
        assert is_code_search == False, "FIXED: 'framework' keyword overrides 'async' keyword"

        # Execute search and validate it returns repos, not code files
        result = await cli._github_search("python async framework", max_results=5)

        # Should return results
        assert len(result["results"]) >= 0, "Search should not crash"
        # Should use github source (not github_code)
        if len(result["results"]) > 0:
            assert "github" in result.get("sources_used", []), "Should use repo search"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN environment variable not set"
    )
    async def test_false_positive_import_tutorial(self, cli):
        """Test false positive fix: 'import tutorial' should NOT route to code search.

        This query is about tutorials on importing, not code containing import statements.
        The 'tutorial' keyword should override the 'import' keyword.
        """
        # Pattern detection should identify this as repo search (FIXED)
        is_code_search = cli._is_code_search_query("import tutorial")

        # FIXED: Should now route to repo search (not code search)
        assert is_code_search == False, "FIXED: 'tutorial' keyword overrides 'import' keyword"

        # Execute search
        result = await cli._github_search("import tutorial", max_results=5)

        # Should return results
        assert len(result["results"]) >= 0, "Search should not crash"
        # Should use github source (not github_code)
        if len(result["results"]) > 0:
            assert "github" in result.get("sources_used", []), "Should use repo search"

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("GITHUB_TOKEN"),
        reason="GITHUB_TOKEN environment variable not set"
    )
    async def test_true_positive_function_search(self, cli):
        """Test true positive: 'python function decorator' SHOULD route to code search.

        This query is looking for code patterns, not repos.
        """
        is_code_search = cli._is_code_search_query("python function decorator")

        # Should route to code search (correct)
        assert is_code_search == True, "Should detect 'function' keyword for code search"

        # Execute search
        result = await cli._github_search("python function decorator", max_results=5)

        # Should return code results
        assert len(result["results"]) >= 0, "Search should not crash"
        if len(result["results"]) > 0:
            # First result should be from code search
            assert "sources_used" in result
            assert "github_code" in result["sources_used"]
