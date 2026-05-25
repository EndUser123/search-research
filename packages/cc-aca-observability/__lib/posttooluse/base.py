#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse Hook Base Module
=============================

Base class for in-process PostToolUse hooks.

All PostToolUse hooks should inherit from PostToolUseHook
and implement the process() method.

This eliminates subprocess overhead (~150ms) by running hooks
in the same process instead of spawning new Python interpreters.

Matcher filtering: hooks define tool_matcher (regex pattern or set of tool names)
to skip execution when the current tool doesn't match. None = match all tools.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

# Configure logger for PostToolUse hooks - no stderr output
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


def is_block_result(result: Any) -> bool:
    """Return True when a hook result requests blocking."""
    if not isinstance(result, dict):
        return False
    return (
        result.get("decision") == "block"
        or result.get("block") is True
        or result.get("allow") is False
    )


class PostToolUseHook(ABC):
    """
    Base class for PostToolUse hooks.

    Hooks are enabled/disabled via environment variables.
    Each hook runs in-process and returns a dict with results.

    Set tool_matcher to limit which tools trigger this hook:
    - None: runs on all tools (default, backward-compatible)
    - set[str]: runs only when tool_name is in the set
    """

    env_var: str | None = None
    default_enabled: bool = True
    # Tool matcher: None = all tools, set = specific tool names
    tool_matcher: set[str] | None = None

    def __init__(self):
        self.enabled = self._check_enabled()

    @staticmethod
    def _normalize_tool_input(value: Any) -> dict[str, Any]:
        """Return a dict-shaped tool_input for downstream hooks."""
        if isinstance(value, dict):
            return value
        return {}

    @staticmethod
    def _normalize_tool_response(value: Any) -> dict[str, Any]:
        """Return a dict-shaped tool_response for downstream hooks.

        Claude Code payloads are not fully consistent here. Some tools return a
        structured dict, while others provide plain strings or scalars. Most
        in-process hooks assume dict access via `.get(...)`, so centralize the
        coercion here instead of forcing each hook to duplicate guards.
        """
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return {"output": value, "result": value}
        return {"output": str(value), "result": value}

    def _check_enabled(self) -> bool:
        """Check if hook is enabled via environment variable."""
        if self.env_var is None:
            return True

        import os

        env_value = os.environ.get(self.env_var, str(self.default_enabled)).lower()
        return env_value in ("1", "true", "yes")

    def matches_tool(self, tool_name: str) -> bool:
        """Check if this hook should run for the given tool."""
        if self.tool_matcher is None:
            return True
        return tool_name in self.tool_matcher

    @abstractmethod
    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process the tool result.

        Args:
            tool_name: Name of the tool that was used
            tool_input: Input parameters passed to the tool
            tool_response: Output returned by the tool

        Returns:
            Dict with results. Common fields:
            - passed: bool (always True for non-blocking hooks)
            - injection: str | None (message to inject into context)
            - metadata: dict (hook-specific data)
        """
        pass

    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Run the hook with parsed input data.

        This is the main entry point called by the router.
        Handles enabled check, matcher filtering, and errors gracefully.
        """
        if not self.enabled:
            return {"passed": True, "skipped": True, "reason": "disabled"}

        tool_name = data.get("tool_name", "")

        # Matcher filtering: skip if tool doesn't match
        if not self.matches_tool(tool_name):
            return {"passed": True, "skipped": True, "reason": "tool_mismatch"}

        tool_input = self._normalize_tool_input(data.get("tool_input", {}))
        raw_response = data.get("tool_response")
        if raw_response in (None, {}, ""):
            raw_response = data.get("tool_result")
        tool_response = self._normalize_tool_response(raw_response)

        try:
            result = self.process(tool_name, tool_input, tool_response)
            # Handle None returns from process() - some hooks return None for no-op cases
            if result is None:
                result = {"passed": True}
            else:
                result.setdefault("passed", True)
            return result
        except Exception as e:
            # Non-blocking: log error details without using stderr
            logger.error(f"[{self.__class__.__name__}] error: {e}", exc_info=False)
            return {"passed": True, "diagnostic": f"{self.__class__.__name__}: {e}"}


class HookRegistry:
    """
    Registry for PostToolUse hooks.

    Provides ordered execution with matcher filtering and error isolation.
    Each hook's error is caught independently — one failure never crashes the router.
    """

    def __init__(self):
        self._hooks: list[tuple[str, PostToolUseHook]] = []

    def register(self, name: str, hook: PostToolUseHook) -> None:
        """Register a hook with a name."""
        self._hooks.append((name, hook))

    def run_all(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Run all registered hooks and collect results.

        Returns combined output with injections from all hooks.
        Matcher filtering happens inside each hook's run() method.
        """
        injections = []

        for name, hook in self._hooks:
            result = hook.run(data)

            # Collect injections for context
            if result.get("injection"):
                injections.append(result["injection"])

            # Check for blocking results (not used by current hooks)
            if is_block_result(result):
                return result

        # Combine injections
        if injections:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": "\n\n".join(injections),
                }
            }

        return {}

    def get_status(self) -> dict[str, bool]:
        """Get enabled status of all registered hooks."""
        return {name: hook.enabled for name, hook in self._hooks}
