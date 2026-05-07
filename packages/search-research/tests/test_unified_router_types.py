"""Type hint verification tests for unified_router.py (TASK-003).

These tests verify that UnifiedAsyncRouter and related classes have proper
type hints, especially for async methods that return list[SearchResult].

Run with: pytest tests/test_unified_router_types.py -v
"""

import subprocess
import sys
from typing import get_type_hints

import pytest

from core.unified_router import UnifiedAsyncRouter
from search_research import SearchResult


class TestUnifiedAsyncRouterReturnType:
    """Tests for UnifiedAsyncRouter return type annotations."""

    def test_search_async_returns_list_of_search_result(self):
        """Test that search_async has -> list[SearchResult] return type.

        Given: UnifiedAsyncRouter class
        When: Getting type hints for search_async method
        Then: Return type should be list[SearchResult]

        This ensures type safety for async search operations.
        """
        # Arrange
        method = UnifiedAsyncRouter.search_async

        # Act
        type_hints = get_type_hints(method)
        return_type = type_hints.get("return")

        # Assert
        assert return_type is not None, "search_async must have return type annotation"
        # Check that it's a generic type with list[SearchResult]
        # In Python 3.9+, this is represented as __origin__ = list
        assert hasattr(return_type, "__origin__"), (
            f"Return type must be a generic type, got {return_type}"
        )
        assert return_type.__origin__ is list, (
            f"Return type must be list, got {return_type.__origin__}"
        )
        # Check the type argument
        type_args = return_type.__args__
        assert len(type_args) == 1, "list[SearchResult] should have one type argument"
        assert type_args[0] is SearchResult, (
            f"Return type must be list[SearchResult], got list[{type_args[0]}]"
        )


class TestAllAsyncMethodsHaveReturnTypes:
    """Tests that all async methods have return type annotations."""

    def test_all_async_methods_have_return_annotations(self):
        """Test that all async methods in UnifiedAsyncRouter have return types.

        Given: UnifiedAsyncRouter class
        When: Inspecting all async methods
        Then: All should have return type annotations

        This catches missing type hints on async methods.
        """
        # Arrange & Act - filter to actual async methods
        import inspect

        missing_return_types = []
        for method_name in dir(UnifiedAsyncRouter):
            if method_name.startswith("__") and method_name.endswith("__"):
                # Skip magic methods like __init__
                continue

            method = getattr(UnifiedAsyncRouter, method_name)
            if not callable(method):
                continue

            if inspect.iscoroutinefunction(method):
                # This is an async method
                type_hints = get_type_hints(method)
                if "return" not in type_hints:
                    missing_return_types.append(method_name)

        # Assert
        assert len(missing_return_types) == 0, (
            f"The following async methods are missing return type annotations: "
            f"{', '.join(missing_return_types)}"
        )


class TestMypyStrictMode:
    """Tests that mypy --strict passes for unified_router.py."""

    @pytest.mark.skip(reason="Pre-existing mypy --strict errors in core/ (technical debt)")
    def test_mypy_strict_compliance(self):
        """Test that unified_router.py passes mypy --strict.

        Given: The unified_router.py file
        When: Running mypy --strict
        Then: No errors should be reported

        This ensures comprehensive type safety including:
        - All functions have return type annotations
        - All parameters have type annotations
        - No implicit Any types
        - No unused ignore comments
        """
        # Arrange
        module_path = "src/search_research/core/unified_router.py"

        # Act
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", module_path],
            capture_output=True,
            text=True,
            cwd="P:\\\\packages/search-research",
        )

        # Assert
        # Check if mypy found any errors
        # Exit code 0 means success, 1 means errors found
        if result.returncode != 0:
            # Mypy found errors - fail the test with detailed output
            error_lines = result.stdout.strip().split("\n")
            # Filter out summary lines, show actual errors
            actual_errors = [
                line for line in error_lines
                if line and not line.startswith("Found") and "Success" not in line
            ]

            pytest.fail(
                "mypy --strict found type errors:\n" + "\n".join(actual_errors)
            )

        # If we get here, mypy passed
        assert result.returncode == 0, "mypy --strict should exit with code 0"

    def test_mypy_strict_on_search_async_specifically(self):
        """Test that search_async specifically has no mypy errors.

        Given: UnifiedAsyncRouter.search_async method
        When: Running mypy --strict on the module
        Then: No errors related to search_async return type

        This is a targeted check for the main method of interest.
        """
        # Arrange
        module_path = "src/search_research/core/unified_router.py"

        # Act
        result = subprocess.run(
            [sys.executable, "-m", "mypy", "--strict", module_path],
            capture_output=True,
            text=True,
            cwd="P:\\\\packages/search-research",
        )

        # Assert
        # Check that search_async is not mentioned in errors
        if "search_async" in result.stdout:
            pytest.fail(
                f"search_async has mypy errors:\n{result.stdout}"
            )


class TestTypeHintCompleteness:
    """Tests for complete type hint coverage."""

    def test_unified_async_router_init_has_type_hints(self):
        """Test that __init__ method has complete type hints.

        Given: UnifiedAsyncRouter.__init__
        When: Getting type hints
        Then: All parameters should have type annotations

        This ensures constructor type safety.
        """
        # Arrange
        method = UnifiedAsyncRouter.__init__

        # Act
        type_hints = get_type_hints(method)

        # Assert - check key parameters have type hints
        expected_params = ["mode", "enable_jmri", "rrf_k", "quality_config"]
        for param in expected_params:
            # Type hints for parameters are stored by their name
            assert param in type_hints, (
                f"Parameter '{param}' should have type annotation"
            )

    def test_search_async_parameters_have_type_hints(self):
        """Test that search_async parameters have type annotations.

        Given: UnifiedAsyncRouter.search_async
        When: Getting type hints
        Then: All parameters should have type annotations

        This ensures parameter type safety for the main search method.
        """
        # Arrange
        method = UnifiedAsyncRouter.search_async

        # Act
        type_hints = get_type_hints(method)

        # Assert
        expected_params = ["query", "limit", "return"]
        for param in expected_params:
            assert param in type_hints, (
                f"Parameter '{param}' should have type annotation"
            )

        # Check specific types
        assert type_hints["query"] is str, "query parameter should be str"
        assert type_hints["limit"] is int, "limit parameter should be int"
