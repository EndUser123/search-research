"""Tests for the Read bypass in PreToolUse_directory_policy.py.

Per session requirement (2026-06-26): Read is never blocked by directory
policy; Write/Edit/Bash retain all five policy layers.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = PLUGIN_ROOT / "hooks" / "pretool" / "PreToolUse_directory_policy.py"
PLUGIN_LIB = PLUGIN_ROOT / "__lib"


@pytest.fixture(scope="module")
def hook():
    """Load the hook with its plugin bootstrap intact.

    The live harness loads hooks through Claude Code's dispatcher, which
    pre-registers `__lib` as an importable package. That gives path_validator.py
    a parent package context for its `from .hook_cache import` line. We
    replicate that here by registering `__lib` as a package and loading
    path_validator under that name before the hook runs.
    """
    # 1. Plugin-local __lib: needed for hooks_resolver (used by bootstrap).
    if str(PLUGIN_LIB) not in sys.path:
        sys.path.insert(0, str(PLUGIN_LIB))

    from hooks_resolver import get_hooks_dir

    global_hooks_dir = get_hooks_dir()
    global_lib = global_hooks_dir / "__lib"

    # 2. Register `__lib` as a real package so relative imports work.
    if "__lib" not in sys.modules:
        import types

        pkg = types.ModuleType("__lib")
        pkg.__path__ = [str(global_lib)]
        sys.modules["__lib"] = pkg

    # 3. Eagerly import path_validator so its top-level relative import
    #    (`from .hook_cache import measure_performance`) resolves under
    #    the __lib package we just registered. The hook itself never calls
    #    measure_performance, so a no-op stub is fine.
    if "hook_cache" not in sys.modules:
        import types

        cache_mod = types.ModuleType("__lib.hook_cache")
        cache_mod.measure_performance = lambda *a, **kw: None
        sys.modules["__lib.hook_cache"] = cache_mod

    # 4. Add the global hooks dir to sys.path so the bootstrap's
    #    `from __lib.hook_base import hook_main` resolves.
    if str(global_hooks_dir) not in sys.path:
        sys.path.insert(0, str(global_hooks_dir))

    spec = importlib.util.spec_from_file_location(
        "PreToolUse_directory_policy", HOOK_PATH
    )
    assert spec and spec.loader, f"cannot load spec for {HOOK_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_read_returns_none(hook):
    """Read bypasses all five policy layers regardless of path."""
    # Path under P:/.pi/ — the path that was being blocked before the bypass.
    result = hook.run(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": "P:/.pi/pi-risk-policy/README.md"},
        },
        False,
    )
    assert result is None, f"Read should not be blocked, got: {result!r}"


def test_read_with_absolute_windows_path_returns_none(hook):
    """Read with backslash Windows path also bypasses."""
    result = hook.run(
        {
            "tool_name": "Read",
            "tool_input": {"file_path": r"P:\.pi\pi-risk-policy\README.md"},
        },
        False,
    )
    assert result is None


def test_read_returns_none_when_policy_disabled(hook, monkeypatch):
    """Hook disabled → still returns None (Read bypass respects enable flag)."""
    monkeypatch.setenv("DIRECTORY_POLICY_ENABLED", "false")
    try:
        result = hook.run(
            {
                "tool_name": "Read",
                "tool_input": {"file_path": "P:/anything"},
            },
            False,
        )
    finally:
        monkeypatch.delenv("DIRECTORY_POLICY_ENABLED", raising=False)
    assert result is None


def test_write_to_project_root_still_blocked(hook):
    """Bypass is surgical: Write on disallowed paths still blocks."""
    result = hook.run(
        {
            "tool_name": "Write",
            "tool_input": {"file_path": "P:/test.py", "content": "x"},
        },
        False,
    )
    assert result is not None, "Write to project root should still be blocked"
    decision = result.get("decision") or result.get("hookSpecificOutput", {}).get(
        "permissionDecision"
    )
    assert decision in ("block", "deny"), f"expected block/deny, got: {decision!r}"