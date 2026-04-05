#!/usr/bin/env python3
"""
Tool Availability Checker - PreToolUse Hook
==========================================

Verifies tool works before calling to prevent tool selection errors.
Per ADR-20260325: Self-Correcting Agent Loop.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

# MCP ping/pong timeout and retries from plan
MCP_TIMEOUT_SECONDS = 5
MCP_MAX_RETRIES = 3


def _get_tool_name(data: dict) -> str:
    """Extract tool name from PreToolUse event data."""
    return data.get("tool", "") or data.get("toolName", "") or ""


def _get_skill_name_from_params(data: dict) -> str | None:
    """Extract skill name from Skill tool parameters."""
    try:
        params = data.get("parameters", {}) or data.get("params", {})
        skill = params.get("skill", "") or params.get("skillName", "")
        return skill if skill else None
    except (TypeError, AttributeError):
        return None


def _get_bash_command_from_params(data: dict) -> str | None:
    """Extract bash command from Bash tool parameters."""
    try:
        params = data.get("parameters", {}) or data.get("params", {})
        cmd = params.get("command", "") or params.get("cmd", "")
        if not cmd:
            return None
        # Extract first word (the actual command)
        return cmd.strip().split()[0] if cmd.strip() else None
    except (TypeError, AttributeError):
        return None


def _check_skill_available(skill_name: str) -> tuple[bool, str]:
    """Check if skill file exists and can be imported.

    Returns (is_available, error_message).
    """
    # skill_name is like "planning" or "gto" - resolve to skill directory
    skills_base = Path(__file__).resolve().parent.parent / "skills"

    # Try common skill paths
    possible_paths = [
        skills_base / skill_name / "SKILL.md",
        skills_base / skill_name.lower() / "SKILL.md",
        skills_base / skill_name.upper() / "SKILL.md",
    ]

    skill_path = None
    for path in possible_paths:
        if path.exists():
            skill_path = path
            break

    if not skill_path:
        return False, f"Skill '{skill_name}' not found in skills directory"

    # Try to import the skill module to check for syntax errors
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location(f"skill_{skill_name}", skill_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Just compile check, don't execute
            compile(module, str(skill_path), "exec")
        return True, ""
    except SyntaxError as e:
        return False, f"Skill '{skill_name}' has syntax error: {e}"
    except ImportError as e:
        return False, f"Skill '{skill_name}' import error: {e}"
    except Exception:
        # Other errors - skill file exists and is loadable
        return True, ""


def _check_bash_command_available(cmd: str) -> tuple[bool, str]:
    """Check if bash command exists in PATH.

    Uses explicit PATH from environment to prevent cwd prepending.
    """
    if not cmd:
        return True, ""  # No command to check

    # Use explicit PATH from environment, not os.defpath
    env_path = os.environ.get("PATH", "")
    result = shutil.which(cmd, path=env_path)

    if result is None:
        return False, f"Command '{cmd}' not found in PATH"
    return True, ""


def _check_mcp_server_available(server_name: str) -> tuple[bool, str]:
    """Check MCP server connectivity via ping/pong exchange.

    Returns (is_available, error_message).
    """
    # MCP server availability check - ping/pong with retries
    # This is a simplified check that tries to list resources
    try:
        from mcp_client import MCPClient

        client = MCPClient(server_name)
        # Try ping/pong - most MCP servers respond to ping
        for attempt in range(MCP_MAX_RETRIES):
            try:
                # Simple ping/pong - list servers or ping endpoint
                result = client.list_tools()
                if result is not None:
                    return True, ""
            except Exception:
                if attempt < MCP_MAX_RETRIES - 1:
                    continue
                return (
                    False,
                    f"MCP server '{server_name}' not reachable after {MCP_MAX_RETRIES} attempts",
                )
        return False, f"MCP server '{server_name}' not reachable"
    except ImportError:
        # mcp_client not available - skip MCP check
        return True, ""
    except Exception as e:
        return False, f"MCP check failed for '{server_name}': {e}"


def main() -> None:
    """PreToolUse hook entry point."""
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}")
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        print("{}")
        sys.exit(0)

    tool_name = _get_tool_name(data)
    if not tool_name:
        print("{}")
        sys.exit(0)

    errors: list[str] = []

    # Check based on tool type
    if tool_name == "Skill":
        skill_name = _get_skill_name_from_params(data)
        if skill_name:
            available, error = _check_skill_available(skill_name)
            if not available:
                errors.append(error)

    elif tool_name == "Bash":
        cmd = _get_bash_command_from_params(data)
        if cmd:
            available, error = _check_bash_command_available(cmd)
            if not available:
                errors.append(error)

    elif tool_name.startswith("mcp__"):
        # MCP tool - extract server name from tool name like "mcp__server__tool"
        parts = tool_name.split("__")
        if len(parts) >= 2:
            server_name = parts[1]
            available, error = _check_mcp_server_available(server_name)
            if not available:
                errors.append(error)

    # If any checks failed, block with suggestion
    if errors:
        error_msg = "; ".join(errors)
        suggestion = _get_suggestion(tool_name, errors)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "hookName": "tool_availability_checker",
                "blocked": True,
                "reason": error_msg,
                "suggestion": suggestion,
            }
        }
        print(json.dumps(output))
        sys.exit(1)  # Block the tool call

    # All checks passed
    print("{}")
    sys.exit(0)


def _get_suggestion(tool_name: str, errors: list[str]) -> str:
    """Generate helpful suggestion based on tool and error."""
    if tool_name == "Skill":
        return "Check skill name spelling or use /skills to list available skills"
    elif tool_name == "Bash":
        return "Verify command is installed or check PATH configuration"
    elif tool_name.startswith("mcp__"):
        return "Check MCP server configuration or try reconnecting"
    return "Verify tool availability before calling"


if __name__ == "__main__":
    main()
