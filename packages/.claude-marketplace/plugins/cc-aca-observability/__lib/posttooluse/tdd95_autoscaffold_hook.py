#!/usr/bin/env python3
"""
PostToolUse TDD-95 Auto-Scaffold Hook

Automatically creates test files when implementation files are written.

Triggers:
- PostToolUse on Write/Edit of implementation files
- Only when test file doesn't exist

Behavior:
1. Detect impl file write
2. Find expected test location(s)
3. If no test exists, create minimal stub
4. Log the scaffold action

Designed for Windows 11, multi-terminal, Python + TypeScript only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path
hooks_dir = Path("P:/.claude/hooks")
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from tdd95_core import (
    TDD95StateManager,
    canonicalize_path,
    cleanup_expired_states,
    get_bypass_flag,
    get_critical_hook_tests,
    get_template_for_impl,
    in_tier,
    is_critical_hook,
    is_exempt,
    load_config,
    path_from_posix,
)


def should_scaffold_for(file_path: Path, config: dict) -> tuple[bool, str]:
    """
    Determine if we should auto-scaffold for this file.

    Returns:
        (should_scaffold, reason)
    """
    # Check bypass flag
    if get_bypass_flag():
        return False, "TDD_BYPASS=1"

    # Check if autoscaffold is enabled
    autoscaffold_config = config.get("autoscaffold", {})
    if not autoscaffold_config.get("enabled", True):
        return False, "autoscaffold disabled"

    # Check if file is exempt
    if is_exempt(file_path, config):
        return False, "file exempt"

    # Check if this is an implementation file
    from tdd95_core import is_impl_file

    if not is_impl_file(file_path, config):
        return False, "not an impl file"

    # Check if in enabled tier
    tier_enabled = False
    for tier_name in ("TIER0", "TIER1"):
        if in_tier(file_path, tier_name, config):
            tier_enabled = True
            action = config.get("tiers", {}).get(tier_name, {}).get("action", "scaffold")
            if action != "scaffold":
                return False, f"tier {tier_name} action is {action}"

    if not tier_enabled:
        return False, "not in enabled tier"

    # Check if file was just created (vs edit)
    # We scaffold on both create and edit if test is missing
    return True, "should scaffold"


def find_best_test_path(impl_path: Path, config: dict) -> Path | None:
    """
    Find the best test path for scaffolding.

    Priority:
    1. Primary test directory (tests/)
    2. Hooks test directory (for hooks/)
    3. First writable location

    Returns:
        Path object or None if no valid location
    """
    from tdd95_core import find_project_root, get_test_candidates

    candidates = get_test_candidates(impl_path, config)

    if not candidates:
        return None

    # Filter to existing parent directories only
    project_root = find_project_root(impl_path)
    if project_root:
        valid_candidates = []
        for c in candidates:
            # Check if parent directory exists
            if c.parent.exists() or c.parent == project_root:
                valid_candidates.append(c)

        if valid_candidates:
            # Return first valid candidate
            return valid_candidates[0]

    # Fall back to first candidate if none are valid
    # (will create directory if needed)
    return candidates[0]


def scaffold_test_file(impl_path: Path, config: dict) -> dict[str, Any]:
    """
    Create a test file for the given implementation file.

    Returns:
        Dict with result info
    """
    test_path = find_best_test_path(impl_path, config)

    if not test_path:
        return {
            "action": "skip",
            "reason": "No valid test path found",
            "impl_file": str(impl_path),
        }

    # Check if test already exists
    if test_path.exists():
        return {
            "action": "skip",
            "reason": "Test file already exists",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
        }

    # Create parent directory if needed
    test_path.parent.mkdir(parents=True, exist_ok=True)

    # Get template
    template_type = config.get("autoscaffold", {}).get("template", "minimal")
    template = get_template_for_impl(impl_path, template_type)

    # Write test file
    try:
        test_path.write_text(template, encoding="utf-8")

        # Update state manager
        state_mgr = TDD95StateManager()
        state_mgr.record_impl_edit(impl_path)

        return {
            "action": "scaffolded",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
            "template_type": template_type,
            "message": f"Auto-scaffolded test: {test_path}",
        }

    except OSError as e:
        return {
            "action": "error",
            "impl_file": str(impl_path),
            "test_file": str(test_path),
            "error": str(e),
            "message": f"Failed to scaffold test: {e}",
        }


def check_critical_hook_tests(impl_path: Path, config: dict) -> dict[str, Any] | None:
    """
    For critical hooks, verify required tests exist.

    Returns None if tests are OK, otherwise returns warning dict.
    """
    if not is_critical_hook(impl_path, config):
        return None

    hook_tests = get_critical_hook_tests(impl_path.stem)

    if not hook_tests:
        return {
            "action": "warning",
            "severity": "critical_hook",
            "message": f"Critical hook {impl_path.name} has no test requirements defined. "
            f"Add to critical_hooks.json or use @critical_hook marker.",
            "impl_file": str(impl_path),
        }

    # Check if required tests exist
    missing_tests = []
    for test_path_str in hook_tests.required_tests:
        test_path = path_from_posix(test_path_str)
        if not test_path.exists():
            missing_tests.append(test_path_str)

    if missing_tests:
        return {
            "action": "critical_tests_missing",
            "severity": "block",
            "message": f"Critical hook {impl_path.name} requires tests: {', '.join(missing_tests)}",
            "impl_file": str(impl_path),
            "missing_tests": missing_tests,
            "required_tests": hook_tests.required_tests,
        }

    return None


def process_write(
    tool_input: dict[str, Any], tool_response: dict[str, Any]
) -> dict[str, Any] | None:
    """
    Process a Write/Edit tool call.

    Returns:
        Result dict or None
    """
    # Get file path from various sources
    file_path_str = (
        tool_input.get("file_path", "")
        or tool_input.get("path", "")
        or tool_response.get("path", "")
        or os.environ.get("CLAUDE_TOOL_EDIT_FILE", "")
        or os.environ.get("CLAUDE_TOOL_WRITE_FILE", "")
    )

    if not file_path_str:
        return None

    impl_path = canonicalize_path(file_path_str)

    # Load config
    config = load_config()

    # Check critical hook requirements first
    critical_check = check_critical_hook_tests(impl_path, config)
    if critical_check:
        return critical_check

    # Check if we should scaffold
    should_scaffold, reason = should_scaffold_for(impl_path, config)

    if not should_scaffold:
        return None

    # Scaffold the test file
    result = scaffold_test_file(impl_path, config)

    # Add debug info
    result["reason"] = reason
    result["config"] = {
        "tier_enabled": in_tier(impl_path, "TIER0", config) or in_tier(impl_path, "TIER1", config),
        "autoscaffold_enabled": config.get("autoscaffold", {}).get("enabled", True),
    }

    return result


def main():
    """
    Hook entry point.

    Reads stdin for hook input, processes Write/Edit operations.
    """
    # Periodic cleanup (done once per invocation)
    try:
        cleaned = cleanup_expired_states()
        if cleaned > 0:
            # Log cleanup count (Optional, for monitoring)
            pass
    except Exception:
        pass  # Don't fail hook on cleanup error

    # Read hook input
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # No valid input, exit cleanly
        print(json.dumps({}))
        return

    tool_name = input_data.get("name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("response", {})

    # Only process Write/Edit operations
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({}))
        return

    result = process_write(tool_input, tool_response)

    if result and result.get("action") not in ("skip",):
        # Output result for visibility
        print(json.dumps(result))
    else:
        print(json.dumps({}))


# =============================================================================
# PostToolUseHook wrapper for registry integration
# =============================================================================

from posttooluse.base import PostToolUseHook


class TDD95AutoScaffoldHook(PostToolUseHook):
    """
    Wrapper class for TDD-95 auto-scaffold hook.

    This wraps the standalone process_write() function in a PostToolUseHook
    interface for registry-based execution.
    """

    tool_matcher: set[str] | None = {"Write", "Edit", "MultiEdit"}

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process Write/Edit tool calls for TDD auto-scaffolding.

        Returns:
            dict with 'injection' key if test was scaffolded, else empty dict
        """
        # Note: tool_name intentionally unused - process_write derives file path from input
        result = process_write(tool_input, tool_response)

        if result is None:
            return {}

        action = result.get("action", "")

        # Only inject message for scaffolded actions
        if action == "scaffolded":
            message = result.get("message", "")
            if message:
                return {"injection": f"Auto-scaffold: {message}"}

        return {}


if __name__ == "__main__":
    main()
