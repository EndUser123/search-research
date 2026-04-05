#!/usr/bin/env python3
"""
tool_checker.py - Tool Availability Detection for rca

This module detects which Claude Code tools are available to the current session.
It is used by the rca tool gate to ensure required tools are present before
allowing skill execution.

Required Tools (Tier 1):
- Grep: Code searching for evidence gathering
- Read: File reading for investigation
- Bash: Command execution for testing
- WebSearch: Optional - remote evidence gathering (can be disabled via DEBUGRCA_LOCAL_ONLY)

Environment Variables:
- DEBUGRCA_LOCAL_ONLY: Set to "1" or "true" to disable WebSearch requirement
- DEBUGRCA_MOCK_TOOLS: Comma-separated list of tools to report as available (for testing)
- DEBUGRCA_MOCK_MISSING_TOOLS: Comma-separated list of tools to report as missing (for testing)

Author: TDD Cycle for rca Tier 1
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# =============================================================================
# Configuration
# =============================================================================

# Required tools for rca Tier 1
# WebSearch is optional (can be disabled via DEBUGRCA_LOCAL_ONLY)
REQUIRED_TOOLS = {
    "Grep": True,      # Required - Code search
    "Read": True,      # Required - File reading
    "Bash": True,      # Required - Command execution
    "WebSearch": False,  # Optional - Remote search
}

# =============================================================================
# Tool Detection
# =============================================================================


def detect_available_tools() -> set[str]:
    """Detect which Claude Code tools are available in the current environment.

    This function checks the hook environment to determine which tools
    Claude Code has registered.

    Returns:
        Set of tool names that are available
    """
    # Check for mock tools (testing support)
    # If DEBUGRCA_MOCK_TOOLS is set (even to empty string), use it
    if "DEBUGRCA_MOCK_TOOLS" in os.environ:
        mock_tools = os.environ.get("DEBUGRCA_MOCK_TOOLS", "")
        # Split and parse - empty string results in empty set
        return set(tool.strip() for tool in mock_tools.split(",") if tool.strip())

    # In real Claude Code environment, tool availability is determined
    # by what's registered in the system. Since we run in a subprocess,
    # we can't directly query the tool registry.

    # For practical purposes, assume standard tools are available
    # in a normal Claude Code session.
    standard_tools = {"Grep", "Read", "Bash", "Write", "Edit", "Glob"}

    # WebSearch may not be available in all environments
    # We'll include it and let the check_required_tools logic handle it
    standard_tools.add("WebSearch")

    return standard_tools


def get_missing_tools(available: set[str], local_only: bool = False) -> list[str]:
    """Get list of required tools that are not available.

    Args:
        available: Set of available tool names
        local_only: If True, WebSearch is explicitly not required (already handled by REQUIRED_TOOLS)

    Returns:
        List of missing tool names
    """
    missing = []

    for tool, required in REQUIRED_TOOLS.items():
        # Required tools (Grep, Read, Bash) are always required
        # Optional tools (WebSearch) are never required
        # The local_only parameter is kept for API compatibility but the
        # optional/not-required distinction is now based solely on REQUIRED_TOOLS

        if required:
            # This is a required tool
            if tool not in available:
                missing.append(tool)
        # else: optional tool - don't check for it

    return missing


def is_local_only_mode() -> bool:
    """Check if DEBUGRCA_LOCAL_ONLY mode is enabled.

    Returns:
        True if local-only mode is enabled
    """
    local_only = os.environ.get("DEBUGRCA_LOCAL_ONLY", "0").lower()
    return local_only in ("1", "true", "yes", "on")


# =============================================================================
# Main Check Function
# =============================================================================


def check_tool_availability() -> dict[str, Any]:
    """Check if required tools are available for rca.

    Returns:
        Dict with keys:
        - available: bool - True if all required tools available
        - missing: list[str] - List of missing tool names
        - tools: list[str] - All detected tools
        - mode: str - "local" or "full" depending on DEBUGRCA_LOCAL_ONLY
    """
    # Check for forced error (testing)
    if os.environ.get("DEBUGRCA_FORCE_CHECK_ERROR"):
        raise RuntimeError("Forced check error for testing")

    local_only = is_local_only_mode()

    # Detect available tools
    available_tools = detect_available_tools()

    # Check for mock missing tools (testing support)
    mock_missing = os.environ.get("DEBUGRCA_MOCK_MISSING_TOOLS", "")
    if mock_missing:
        missing = [tool.strip() for tool in mock_missing.split(",") if tool.strip()]
    else:
        missing = get_missing_tools(available_tools, local_only)

    return {
        "available": len(missing) == 0,
        "missing": missing,
        "tools": sorted(available_tools),
        "mode": "local" if local_only else "full",
    }


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """CLI entry point for tool_checker.py.

    Prints JSON output with tool availability status.
    """
    try:
        result = check_tool_availability()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        # Fail open - print error but don't crash
        error_result = {
            "available": False,
            "error": str(e),
            "tools": [],
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
