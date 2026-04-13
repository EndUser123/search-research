#!/usr/bin/env python3
"""Auto-logging decorator for hook exception handling.

Provides a decorator that wraps hook main() functions with automatic
exception logging, ensuring all failures are captured in cc_errors.jsonl.

Also provides the in-process hook protocol for modernized hook execution.

## Subprocess Mode (Legacy)

Usage:
    from __lib.hook_base import hook_main, set_hook_context

    @hook_main
    def main():
        # Parse stdin first
        data = json.loads(sys.stdin.read())

        # Set context for error logging (call early, before potential failures)
        set_hook_context(
            user_prompt=data.get("prompt"),
            claude_session_id=data.get("session_id")
        )

        # Hook logic - exceptions auto-logged with context
        ...

    if __name__ == "__main__":
        main()

## In-Process Mode (Phase 1 Modernization)

Hooks can expose a `run(data) -> dict | None` function for direct in-process
calling by Stop_router.py, eliminating subprocess overhead.

Protocol:
    - Implement: def run(data: dict) -> dict | None
    - Return: {"block": True, "reason": "..."} to block
    - Return: {"allow": True} or None to allow
    - Exceptions: Caught and logged via cc_errors.jsonl

Example:
    @hook_main
    def main():
        # Legacy subprocess entry point
        data = json.loads(sys.stdin.read())
        result = run(data)  # Call shared logic
        print(json.dumps(result))

    def run(data: dict) -> dict | None:
        # In-process callable
        prompt = data.get("response", "")
        if "TODO" in prompt:
            return {"block": True, "reason": "TODO detected"}
        return None

FAIL-FAST POLICY:
    ALL errors fail immediately with exit code 1. No masking, no graceful
    degradation. Hook failures surface immediately for debugging.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import sys
import traceback
from pathlib import Path
from threading import local

_script_path = Path(__file__)
for _hooks_root in (
    Path(r"P:\.claude\hooks"),
    _script_path.parent.parent,
    _script_path.resolve().parent.parent,
):
    _hooks_root_str = str(_hooks_root)
    if _hooks_root_str not in sys.path:
        sys.path.insert(0, _hooks_root_str)

# Canonical terminal ID normalization (prevents cross-package prefix mismatch)
try:
    from __lib.terminal_id import normalize_terminal_id
except ImportError:
    _terminal_id_path = _script_path.parent / "terminal_id.py"
    _terminal_id_spec = importlib.util.spec_from_file_location(
        "_hooks_terminal_id", _terminal_id_path
    )
    if _terminal_id_spec is None or _terminal_id_spec.loader is None:
        from terminal_id import normalize_terminal_id  # type: ignore
    else:
        _terminal_id_module = importlib.util.module_from_spec(_terminal_id_spec)
        _terminal_id_spec.loader.exec_module(_terminal_id_module)
        normalize_terminal_id = _terminal_id_module.normalize_terminal_id

# Thread-local storage for hook context (user_prompt, claude_session_id)
_hook_context = local()


def set_hook_context(user_prompt: str | None = None, claude_session_id: str | None = None) -> None:
    """Set context for error logging. Call this early in your hook after parsing stdin.

    Args:
        user_prompt: The user's prompt text (for traceability)
        claude_session_id: Claude Code's session_id from hook input
    """
    _hook_context.user_prompt = user_prompt
    _hook_context.claude_session_id = claude_session_id


def get_hook_context() -> dict:
    """Get the current hook context for error logging."""
    return {
        "user_prompt": getattr(_hook_context, "user_prompt", None),
        "claude_session_id": getattr(_hook_context, "claude_session_id", None),
    }


def _get_log_error():
    """Lazy import to avoid circular dependencies."""
    try:
        # Add hooks dir to path for import
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        from cc_diagnostic_logger import log_error

        return log_error
    except ImportError as e:
        # FAIL-FAST: cc_diagnostic_logger is required for hook operation
        print(
            f"[HOOK_BASE] FATAL: cc_diagnostic_logger not available: {e}",
            file=sys.stderr,
        )
        sys.exit(1)


def hook_main(func):
    """Decorator that wraps hook main() with auto-logging on exception.

    Behavior:
    - Logs ALL exceptions to cc_errors.jsonl with full stack trace
    - Includes user_prompt and claude_session_id if set via set_hook_context()
    - Exits with code 1 on ANY error (fail fast, no masking)
    - Prints error details to stderr for immediate visibility
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract hook name from script path
            hook_name = Path(sys.argv[0]).stem if sys.argv else "unknown_hook"

            # Get context if set by the hook
            ctx = get_hook_context()

            # Log the error to cc_errors.jsonl
            log_error = _get_log_error()
            log_error(
                error_type=f"{hook_name}_error",
                error_message=str(e),
                context={"hook": hook_name},
                stack_trace=traceback.format_exc(),
                user_prompt=ctx.get("user_prompt"),
                claude_session_id=ctx.get("claude_session_id"),
            )

            # Print to stderr for immediate visibility
            print(f"[HOOK_ERROR] {hook_name}: {type(e).__name__}: {e}", file=sys.stderr)

            # Fail fast - exit with error code
            print(json.dumps({"ok": False, "error": str(e)}))
            sys.exit(1)

    return wrapper


# =============================================================================
# IN-PROCESS HOOK PROTOCOL (Phase 1 Modernization)
# =============================================================================

import threading
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


class HookTimeoutError(TimeoutError):
    """Hook execution exceeded timeout limit."""

    def __init__(self, hook_name: str, timeout_seconds: float) -> None:
        super().__init__(f"{hook_name} exceeded timeout of {timeout_seconds}s")
        self.hook_name = hook_name
        self.timeout_seconds = timeout_seconds


def run_hook_inprocess(
    hook_name: str,
    hook_data: Mapping[str, Any],
    timeout_seconds: float = 5.0,
) -> dict | None:
    """Run a hook in-process using its `run(data)` protocol.

    This function calls hooks directly without subprocess overhead, providing
    significant latency reduction for Stop hooks. Falls back to subprocess
    mode if the hook doesn't support in-process execution.

    Args:
        hook_name: Name of the hook module (e.g., "empirical_claims_gate")
        hook_data: Data to pass to hook's run() function
        timeout_seconds: Maximum execution time before timeout

    Returns:
        Hook result dict, or None if hook allows action

    Raises:
        HookTimeoutError: If hook execution exceeds timeout
        ImportError: If hook module cannot be imported
        Exception: If hook run() function raises an unexpected exception

    Examples:
        >>> result = run_hook_inprocess("empirical_claims_gate", {"response": "text"})
        >>> if result and result.get("block"):
        ...     print(f"Blocked: {result['reason']}")
    """
    hooks_dir = Path(__file__).resolve().parent.parent

    # Import the hook module
    hook_module = _import_hook_module(hooks_dir, hook_name)
    if hook_module is None:
        raise ImportError(f"Hook module not found: {hook_name}")

    # Check if hook supports in-process protocol
    run_func = getattr(hook_module, "run", None)
    if run_func is None or not callable(run_func):
        return None  # Hook doesn't support in-process mode

    # Execute with timeout using threading.Timer
    result_container: list[dict | None] = []
    exception_container: list[Exception] = []

    def target() -> None:
        """Execute hook in separate thread to enable timeout."""
        try:
            result = run_func(dict(hook_data))
            result_container.append(result)
        except Exception as e:
            exception_container.append(e)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    # Check timeout
    if thread.is_alive():
        # Thread still running = timeout exceeded
        raise HookTimeoutError(hook_name, timeout_seconds)

    # Check for exceptions
    if exception_container:
        raise exception_container[0]

    # Return result (None if container empty = hook allowed action)
    return result_container[0] if result_container else None


def _import_hook_module(hooks_dir: Path, hook_name: str) -> Any | None:
    """Import a hook module by name.

    Args:
        hooks_dir: Directory containing hook modules
        hook_name: Name of hook (with or without .py extension)

    Returns:
        Imported module object, or None if import fails
    """
    import importlib.util

    # Normalize hook name
    if hook_name.endswith(".py"):
        hook_name = hook_name[:-3]

    # Try direct import first (for hooks in root hooks/ directory)
    try:
        spec = importlib.util.spec_from_file_location(hook_name, hooks_dir / f"{hook_name}.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[hook_name] = module
            spec.loader.exec_module(module)
            return module
    except (ImportError, FileNotFoundError, SyntaxError):
        pass

    # Try __lib subdirectory
    try:
        spec = importlib.util.spec_from_file_location(
            hook_name, hooks_dir / "__lib" / f"{hook_name}.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[hook_name] = module
            spec.loader.exec_module(module)
            return module
    except (ImportError, FileNotFoundError, SyntaxError):
        pass

    return None


def supports_inprocess(hook_name: str) -> bool:
    """Check if a hook supports in-process execution.

    Args:
        hook_name: Name of the hook module

    Returns:
        True if hook has a callable `run()` function
    """
    hooks_dir = Path(__file__).resolve().parent.parent
    hook_module = _import_hook_module(hooks_dir, hook_name)
    if hook_module is None:
        return False
    return callable(getattr(hook_module, "run", None))


# =============================================================================
# TERMINAL ID MANAGEMENT (Phase 1: Multi-Terminal Isolation)
# =============================================================================

import hashlib
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

# Terminal ID sanitization regex (alphanumeric and underscore only)
TERMINAL_ID_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_]")


def get_terminal_id(data: Mapping[str, Any] | None = None) -> str:
    """
    Get standardized terminal ID from hook data.

    This is the centralized source of truth for terminal ID generation across
    all hooks. It provides consistent terminal ID derivation with a priority
    order that allows explicit override while falling back to unique process
    identification.

    Priority Order:
    1. Explicit terminal_id from hook input data
    2. CLAUDE_TERMINAL_ID environment variable (highest priority env var)
    3. TERMINAL_ID, TERM_ID, SESSION_TERMINAL environment variables
    4. Console detection (WT_SESSION, GetConsoleWindow on Windows)
    5. Derive from PID + session timestamp (unique per process)
    6. Return "" if no detection method succeeds (callers must handle empty string)

    Args:
        data: Hook input data dictionary (may contain terminal_id, session_start_ts)

    Returns:
        Terminal ID string in normalized format ({source}_{id}) or empty string
        Format examples:
        - "env_abc123" (from environment variable)
        - "console_1a2b3c" (from Windows console handle)
        - "abc123def456" (12-char hex from PID+timestamp derivation)

    Examples:
        >>> # Case 1: Explicit terminal_id in hook data
        >>> get_terminal_id({"terminal_id": "env_custom_123"})
        'env_custom_123'

        >>> # Case 2: Environment variable
        >>> os.environ["CLAUDE_TERMINAL_ID"] = "env_override"
        >>> get_terminal_id({})
        'env_override'

        >>> # Case 3: Derive from process attributes
        >>> tid = get_terminal_id({"session_start_ts": 1234567890})
        >>> len(tid) == 12  # 12-char hex string
        True

    Note:
        Terminal IDs are cached in _hook_context for performance after first call.
        Subsequent calls within the same hook execution return the cached value.
        Explicit terminal_id in data always overrides cache.
    """
    data = data or {}
    terminal_id = ""

    # Priority 1: Explicit terminal_id from hook input data (overrides cache)
    if "terminal_id" in data:
        raw_id = str(data["terminal_id"]).strip()
        if raw_id:
            # Sanitize and normalize
            sanitized = TERMINAL_ID_SANITIZE_RE.sub("", raw_id)
            if sanitized:
                terminal_id = normalize_terminal_id(sanitized)
                # Update cache with explicit value
                _hook_context.terminal_id = terminal_id
                return terminal_id

    # Check cache for non-explicit calls (performance optimization)
    cached_terminal_id = getattr(_hook_context, "terminal_id", None)
    if cached_terminal_id is not None:
        return cached_terminal_id

    # Priority 2: Environment variables (in priority order)
    for env_var in ["CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL"]:
        value = os.environ.get(env_var, "").strip()
        if value:
            terminal_id = normalize_terminal_id(value)
            break

    # Priority 3: Console detection (Windows-specific, persistent)
    if not terminal_id:
        try:
            # Lazy import to avoid circular dependency
            from terminal_detection import detect_console_host_terminal

            console_handle = detect_console_host_terminal()
            if console_handle:
                terminal_id = normalize_terminal_id(console_handle)
        except ImportError:
            # terminal_detection module not available - skip console detection
            pass

    # Priority 4: Derive from process attributes (PID + session timestamp)
    if not terminal_id:
        try:
            pid = os.getpid()
            session_start = data.get("session_start_ts", int(time.time()))
            # Combine PID and timestamp for uniqueness
            unique = f"{pid}_{session_start}".encode()
            terminal_id = hashlib.sha1(unique).hexdigest()[:12]
        except Exception:
            # Fallback: return empty string if derivation fails
            terminal_id = ""

    # Cache in thread-local context for subsequent calls
    if terminal_id:
        os.environ["CLAUDE_TERMINAL_ID"] = terminal_id
    _hook_context.terminal_id = terminal_id

    return terminal_id
