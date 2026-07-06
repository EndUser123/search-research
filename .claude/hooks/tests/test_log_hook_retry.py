"""Regression tests for log_hook._retry_on_locked.

Covers:
  1. Success on first attempt (no retry).
  2. Retries on PermissionError, then raises LockRetryExhausted.
  3. Retries on OSError with winerror == 32, then raises LockRetryExhausted.
  4. Non-lock errors (e.g. ValueError) propagate immediately without retry.
  5. max_attempts is honored.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

_HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import log_hook  # noqa: E402


def _make_oserror(winerror: int) -> OSError:
    err = OSError("simulated lock")
    err.winerror = winerror  # type: ignore[attr-defined]
    return err


def test_success_on_first_call() -> None:
    func = MagicMock(return_value="ok")
    result = log_hook._retry_on_locked(func, "arg", kw="val")
    assert result == "ok"
    func.assert_called_once_with("arg", kw="val")


def test_permission_error_retries_then_exhausts() -> None:
    func = MagicMock(side_effect=PermissionError("locked"))
    try:
        log_hook._retry_on_locked(func, max_attempts=3)
    except log_hook.LockRetryExhausted as exc:
        assert exc.attempts == 3
        assert isinstance(exc.last_error, PermissionError)
    else:
        raise AssertionError("LockRetryExhausted not raised")
    assert func.call_count == 3


def test_oserror_winerror_32_retries_then_exhausts() -> None:
    err = _make_oserror(32)
    func = MagicMock(side_effect=err)
    try:
        log_hook._retry_on_locked(func, max_attempts=2)
    except log_hook.LockRetryExhausted as exc:
        assert exc.attempts == 2
        assert exc.last_error is err
    else:
        raise AssertionError("LockRetryExhausted not raised")
    assert func.call_count == 2


def test_non_lock_error_propagates_immediately() -> None:
    func = MagicMock(side_effect=ValueError("not a lock"))
    try:
        log_hook._retry_on_locked(func, max_attempts=5)
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError should propagate")
    func.assert_called_once()


def test_max_attempts_honored() -> None:
    func = MagicMock(side_effect=PermissionError("locked"))
    for n in (1, 2, 4):
        func.reset_mock()
        try:
            log_hook._retry_on_locked(func, max_attempts=n)
        except log_hook.LockRetryExhausted:
            pass
        else:
            raise AssertionError(f"expected LockRetryExhausted for max_attempts={n}")
        assert func.call_count == n, (
            f"expected {n} attempts, got {func.call_count}"
        )
