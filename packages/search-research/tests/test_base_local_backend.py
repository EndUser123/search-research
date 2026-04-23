"""Auto-scaffolded test for base_local_backend."""

import pytest
from core.backends.local.base_local_backend import BaseLocalBackend


def test_sanitize_query_basic():
    """_sanitize_query strips non-printable and limits length."""
    backend = BaseLocalBackend()
    result = backend._sanitize_query("hello world")
    assert result == "hello world"


def test_sanitize_query_removes_non_printable():
    """_sanitize_query removes non-printable characters."""
    backend = BaseLocalBackend()
    result = backend._sanitize_query("hello\x00world\n\r")
    assert result == "helloworld"


def test_sanitize_query_respects_max_length():
    """_sanitize_query respects max_length parameter."""
    backend = BaseLocalBackend()
    result = backend._sanitize_query("a" * 1000, max_length=10)
    assert result == "a" * 10


def test_sanitize_query_default_max_length():
    """_sanitize_query defaults to 500 chars."""
    backend = BaseLocalBackend()
    result = backend._sanitize_query("a" * 600)
    assert len(result) == 500
