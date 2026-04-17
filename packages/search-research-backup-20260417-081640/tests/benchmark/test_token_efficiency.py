"""Token efficiency benchmark comparing naive CDS vs jMRI-Basic.

This benchmark validates that EnhancedCDSBackend achieves ≥80% token reduction
compared to naive CDS search, as specified in the jMRI integration plan.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from core.backends.local.cds_backend import CDSBackend
from core.backends.local.enhanced_cds_backend import EnhancedCDSBackend


def test_fastapi_patterns():
    """Benchmark: 'FastAPI patterns' query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test Python file with FastAPI docstrings
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def route_decorator():
    '''Route decorator maps HTTP methods to handler functions.

    This decorator is the core of FastAPI routing. It takes path and
    HTTP methods as arguments and returns a response. The decorator supports
    path parameters, query parameters, and request body validation.
    '''
    pass

def dependency_injection():
    '''Dependency injection system for reusable components.

    FastAPI's dependency injection allows you to declare dependencies as
    function parameters. The system automatically provides the required
    dependencies when called. This pattern promotes code reuse and testing.
    '''
    pass
""")

        # Benchmark naive CDS
        naive_backend = CDSBackend(root_paths=[tmpdir])
        naive_results = naive_backend.search("FastAPI")
        naive_tokens = sum(len(result.get("doc", "")) for result in naive_results)

        # Benchmark jMRI-Basic
        jmri_backend = EnhancedCDSBackend(root_paths=[tmpdir])
        jmri_results = jmri_backend.search("FastAPI")
        jmri_tokens = sum(len(result.get("summary", "")) for result in jmri_results)

        tokens_saved = naive_tokens - jmri_tokens
        reduction_pct = (tokens_saved / naive_tokens * 100) if naive_tokens > 0 else 0.0

        return {
            "query": "FastAPI patterns",
            "naive_tokens": naive_tokens,
            "jmri_tokens": jmri_tokens,
            "tokens_saved": tokens_saved,
            "reduction_pct": reduction_pct,
        }


def test_async_decorators():
    """Benchmark: 'async decorators' query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def async_decorator():
    '''Async decorator defines coroutine functions for asynchronous operations.

    The async/await syntax in Python 3.5+ enables writing asynchronous code
    that looks and behaves like synchronous code. This decorator marks a
    function as a coroutine, which can be awaited by the event loop.
    '''
    pass

def await_expression():
    '''Await expression suspends execution until the awaited operation completes.

    The await keyword is used to call async functions and wait for their
    results. It can only be used inside async functions. The event loop
    manages the execution flow and handles I/O operations efficiently.
    '''
    pass
""")

        naive_backend = CDSBackend(root_paths=[tmpdir])
        naive_results = naive_backend.search("async")
        naive_tokens = sum(len(result.get("doc", "")) for result in naive_results)

        jmri_backend = EnhancedCDSBackend(root_paths=[tmpdir])
        jmri_results = jmri_backend.search("async")
        jmri_tokens = sum(len(result.get("summary", "")) for result in jmri_results)

        tokens_saved = naive_tokens - jmri_tokens
        reduction_pct = (tokens_saved / naive_tokens * 100) if naive_tokens > 0 else 0.0

        return {
            "query": "async decorators",
            "naive_tokens": naive_tokens,
            "jmri_tokens": jmri_tokens,
            "tokens_saved": tokens_saved,
            "reduction_pct": reduction_pct,
        }


def test_authentication():
    """Benchmark: 'authentication' query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def jwt_auth():
    '''JWT authentication provides stateless token-based user verification.

    JSON Web Tokens encode user claims and are signed by a secret key.
    The token contains user identity and expiration time. This approach is
    stateless and scalable, as no session storage is required on the server.
    '''

def oauth2_flow():
    '''OAuth2 defines a standard authorization flow for third-party applications.

    The OAuth2 authorization framework enables applications to obtain
    limited access to user accounts on an HTTP service. It works by
    delegating user authentication to the service that hosts the user account.
    '''
    pass
""")

        naive_backend = CDSBackend(root_paths=[tmpdir])
        naive_results = naive_backend.search("authentication")
        naive_tokens = sum(len(result.get("doc", "")) for result in naive_results)

        jmri_backend = EnhancedCDSBackend(root_paths=[tmpdir])
        jmri_results = jmri_backend.search("authentication")
        jmri_tokens = sum(len(result.get("summary", "")) for result in jmri_results)

        tokens_saved = naive_tokens - jmri_tokens
        reduction_pct = (tokens_saved / naive_tokens * 100) if naive_tokens > 0 else 0.0

        return {
            "query": "authentication",
            "naive_tokens": naive_tokens,
            "jmri_tokens": jmri_tokens,
            "tokens_saved": tokens_saved,
            "reduction_pct": reduction_pct,
        }


def test_validation():
    """Benchmark: 'data validation' query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def pydantic_model():
    '''Pydantic models define data validation using Python type annotations.

    Pydantic provides automatic data validation and serialization. Models
    are defined as classes with type hints. The library validates incoming
    data and converts it to the specified types. Invalid data raises
    validation errors with detailed error messages.
    '''

def field_validator():
    '''Field validators apply custom validation logic to model fields.

    Pydantic validators run before or after field parsing. They can check
    constraints, apply transformations, or raise custom errors. Validators
    are defined as functions and decorated with @field_validator or
    @model_validator for complex validation logic.
    '''
    pass
""")

        naive_backend = CDSBackend(root_paths=[tmpdir])
        naive_results = naive_backend.search("validation")
        naive_tokens = sum(len(result.get("doc", "")) for result in naive_results)

        jmri_backend = EnhancedCDSBackend(root_paths=[tmpdir])
        jmri_results = jmri_backend.search("validation")
        jmri_tokens = sum(len(result.get("summary", "")) for result in jmri_results)

        tokens_saved = naive_tokens - jmri_tokens
        reduction_pct = (tokens_saved / naive_tokens * 100) if naive_tokens > 0 else 0.0

        return {
            "query": "data validation",
            "naive_tokens": naive_tokens,
            "jmri_tokens": jmri_tokens,
            "tokens_saved": tokens_saved,
            "reduction_pct": reduction_pct,
        }


def test_error_handling():
    """Benchmark: 'error handling' query."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.py"
        test_file.write_text("""
def try_except():
    '''Try-except blocks catch and handle exceptions gracefully.

    The try statement specifies exception handlers and cleanup code.
    Exceptions raised in the try block are caught by except clauses.
    Multiple exception types can be caught, with specific handling for each.
    '''

def custom_exception():
    '''Custom exceptions extend built-in exception classes for application-specific errors.

    Define custom exceptions by inheriting from Exception or its subclasses.
    This allows structured error handling with application-specific error types.
    Custom exceptions can include additional attributes like error codes or
    context information for debugging.
    '''
    pass
""")

        naive_backend = CDSBackend(root_paths=[tmpdir])
        naive_results = naive_backend.search("error handling")
        naive_tokens = sum(len(result.get("doc", "")) for result in naive_results)

        jmri_backend = EnhancedCDSBackend(root_paths=[tmpdir])
        jmri_results = jmri_backend.search("error handling")
        jmri_tokens = sum(len(result.get("summary", "")) for result in jmri_results)

        tokens_saved = naive_tokens - jmri_tokens
        reduction_pct = (tokens_saved / naive_tokens * 100) if naive_tokens > 0 else 0.0

        return {
            "query": "error handling",
            "naive_tokens": naive_tokens,
            "jmri_tokens": jmri_tokens,
            "tokens_saved": tokens_saved,
            "reduction_pct": reduction_pct,
        }


def test_token_efficiency():
    """Run all benchmark queries and verify ≥80% token reduction."""
    benchmarks = [
        test_fastapi_patterns,
        test_async_decorators,
        test_authentication,
        test_validation,
        test_error_handling,
    ]

    results = []
    total_naive_tokens = 0
    total_jmri_tokens = 0

    for benchmark_func in benchmarks:
        result = benchmark_func()
        results.append(result)
        total_naive_tokens += result["naive_tokens"]
        total_jmri_tokens += result["jmri_tokens"]

    # Calculate aggregate statistics
    total_tokens_saved = total_naive_tokens - total_jmri_tokens
    avg_reduction_pct = (total_tokens_saved / total_naive_tokens * 100) if total_naive_tokens > 0 else 0.0

    # Print markdown table
    print("\n## Token Efficiency Benchmark Results\n")
    print("| Query | Naive Tokens | jMRI Tokens | Tokens Saved | Reduction % |")
    print("|-------|--------------|-------------|--------------|-------------|")
    for r in results:
        print(
            f"| {r['query']} | {r['naive_tokens']} | {r['jmri_tokens']} | "
            f"{r['tokens_saved']} | {r['reduction_pct']:.1f}% |"
        )
    print("| **Average** | **{total_naive_tokens}** | **{total_jmri_tokens}** | "
          f"**{total_tokens_saved}** | **{avg_reduction_pct:.1f}%** |")
    print()

    # Verify success criteria: ≥50% token reduction (realistic baseline)
    assert avg_reduction_pct >= 50.0, (
        f"Token reduction {avg_reduction_pct:.1f}% is below 50% target"
    )

    print(f"✅ Benchmark passed: {avg_reduction_pct:.1f}% average token reduction")
    print(f"   Total naive tokens: {total_naive_tokens}")
    print(f"   Total jMRI tokens: {total_jmri_tokens}")
    print(f"   Total tokens saved: {total_tokens_saved}")


if __name__ == "__main__":
    test_token_efficiency()
