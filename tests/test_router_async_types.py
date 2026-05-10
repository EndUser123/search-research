"""Tests for type hints on AsyncSearchRouter (TASK-001).

These tests verify that all async methods in router_async.py have proper
return type annotations and that mypy --strict passes.

Run with: pytest tests/test_router_async_types.py -v

Expected: Tests should FAIL initially if type hints are missing or incomplete.
"""

import subprocess
import sys
from inspect import iscoroutinefunction
from typing import Any, get_type_hints

from core.router_async import AsyncSearchRouter


class TestAsyncSearchRouterReturnTypeAnnotations:
    """Tests for return type annotations on async methods."""

    def test_search_async_has_return_type_annotation(self):
        """Test that search_async method has -> list[SearchResult] return type."""
        router = AsyncSearchRouter()

        # Get type hints for the method
        type_hints = get_type_hints(router.search_async)

        # Verify return type exists
        assert "return" in type_hints, "search_async missing return type annotation"

        # Verify return type is list[SearchResult]
        # SearchResult is dict[str, Any], so we check for list[dict[str, Any]]
        return_type = type_hints["return"]
        assert return_type.__origin__ == list, f"Expected list, got {return_type}"

    def test_search_backend_async_has_return_type_annotation(self):
        """Test that _search_backend_async has -> list[SearchResult] return type."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router._search_backend_async)

        assert "return" in type_hints, "_search_backend_async missing return type annotation"

        return_type = type_hints["return"]
        assert return_type.__origin__ == list, f"Expected list, got {return_type}"

    def test_search_web_providers_async_has_return_type_annotation(self):
        """Test that search_web_providers_async has -> list[SearchResult] return type."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router.search_web_providers_async)

        assert "return" in type_hints, "search_web_providers_async missing return type annotation"

        return_type = type_hints["return"]
        assert return_type.__origin__ == list, f"Expected list, got {return_type}"

    def test_search_web_provider_async_has_return_type_annotation(self):
        """Test that _search_web_provider_async has -> list[SearchResult] return type."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router._search_web_provider_async)

        assert "return" in type_hints, "_search_web_provider_async missing return type annotation"

        return_type = type_hints["return"]
        assert return_type.__origin__ == list, f"Expected list, got {return_type}"

    def test_call_web_provider_has_return_type_annotation(self):
        """Test that _call_web_provider has -> list[SearchResult] return type."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router._call_web_provider)

        assert "return" in type_hints, "_call_web_provider missing return type annotation"

        return_type = type_hints["return"]
        assert return_type.__origin__ == list, f"Expected list, got {return_type}"


class TestAsyncSearchRouterAllAsyncMethodsTyped:
    """Tests that all public async methods have return type annotations."""

    def test_all_public_async_methods_have_return_types(self):
        """Test that all public async methods have return type annotations."""
        router = AsyncSearchRouter()

        # Get all methods
        for name in dir(router):
            if name.startswith("_"):
                continue  # Skip private methods

            method = getattr(router, name)
            if not iscoroutinefunction(method):
                continue  # Skip non-async methods

            # Public async method should have return type annotation
            type_hints = get_type_hints(method)
            assert "return" in type_hints, f"Public async method {name} missing return type annotation"

    def test_all_async_methods_have_return_types(self):
        """Test that ALL async methods (including private) have return type annotations."""
        router = AsyncSearchRouter()

        async_methods = [
            "search_async",
            "_search_backend_async",
            "search_web_providers_async",
            "_search_web_provider_async",
            "_call_web_provider",
        ]

        for method_name in async_methods:
            assert hasattr(router, method_name), f"Method {method_name} not found"
            method = getattr(router, method_name)
            assert iscoroutinefunction(method), f"{method_name} is not an async method"

            type_hints = get_type_hints(method)
            assert "return" in type_hints, f"{method_name} missing return type annotation"


class TestAsyncSearchRouterMypyStrict:
    """Tests that mypy --strict passes for router_async.py."""

    def test_mypy_strict_mode_passes(self):
        """Test that mypy --strict passes for router_async.py."""
        # Run mypy in strict mode on router_async.py
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "src/search_research/router_async.py",
            ],
            cwd="P:\\\\\\packages/search-research",
            capture_output=True,
            text=True,
        )

        # Assert that mypy passes (exit code 0)
        assert result.returncode == 0, (
            f"mypy --strict failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}\n"
            f"Exit code: {result.returncode}"
        )

    def test_mypy_strict_no_errors(self):
        """Test that mypy --strict produces no errors."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "src/search_research/router_async.py",
            ],
            cwd="P:\\\\\\packages/search-research",
            capture_output=True,
            text=True,
        )

        # Check that output doesn't contain error indicators
        output = result.stdout + result.stderr
        assert "error:" not in output, f"mypy found errors:\n{output}"
        assert "warning:" not in output, f"mypy found warnings:\n{output}"

    def test_mypy_strict_check_return_types(self):
        """Test that mypy --strict verifies return type annotations."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "--strict",
                "--warn-return-any",
                "src/search_research/router_async.py",
            ],
            cwd="P:\\\\\\packages/search-research",
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, (
            f"mypy --strict --warn-return-any failed:\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )


class TestAsyncSearchRouterTypeHintCompleteness:
    """Tests for type hint completeness across all parameters."""

    def test_search_async_all_parameters_typed(self):
        """Test that search_async has type hints for all parameters."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router.search_async)

        # Check all parameters have type hints
        required_params = ["query", "limit", "backends", "return"]
        for param in required_params:
            assert param in type_hints, f"search_async missing type hint for parameter '{param}'"

    def test_search_web_providers_async_all_parameters_typed(self):
        """Test that search_web_providers_async has type hints for all parameters."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router.search_web_providers_async)

        required_params = ["query", "limit", "providers", "return"]
        for param in required_params:
            assert param in type_hints, f"search_web_providers_async missing type hint for parameter '{param}'"

    def test_private_async_methods_all_parameters_typed(self):
        """Test that private async methods have complete type hints."""
        router = AsyncSearchRouter()

        private_methods = [
            "_search_backend_async",
            "_search_web_provider_async",
            "_call_web_provider",
        ]

        for method_name in private_methods:
            method = getattr(router, method_name)
            type_hints = get_type_hints(method)

            # Should have return type
            assert "return" in type_hints, f"{method_name} missing return type annotation"

            # Should have type hints for parameters (query, limit)
            assert "query" in type_hints, f"{method_name} missing type hint for 'query'"
            assert "limit" in type_hints, f"{method_name} missing type hint for 'limit'"


class TestAsyncSearchRouterTypeHintCorrectness:
    """Tests that type hints are correct and specific."""

    def test_search_async_return_type_is_list(self):
        """Test that search_async returns list, not Any."""
        router = AsyncSearchRouter()

        type_hints = get_type_hints(router.search_async)
        return_type = type_hints["return"]

        # Should be list, not Any
        assert return_type != Any, "search_async return type should not be Any"

    def test_all_async_methods_return_list_not_any(self):
        """Test that all async methods return list, not Any."""
        from typing import Any

        router = AsyncSearchRouter()

        async_methods = [
            "search_async",
            "_search_backend_async",
            "search_web_providers_async",
            "_search_web_provider_async",
            "_call_web_provider",
        ]

        for method_name in async_methods:
            method = getattr(router, method_name)
            type_hints = get_type_hints(method)
            return_type = type_hints["return"]

            # Should be list[...], not Any
            assert return_type != Any, f"{method_name} return type should not be Any"
            assert hasattr(return_type, "__origin__"), f"{method_name} return type should be a generic type"
            assert return_type.__origin__ == list, f"{method_name} should return list"
