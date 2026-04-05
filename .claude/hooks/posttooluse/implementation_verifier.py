#!/usr/bin/env python3
"""
ImplementationVerifier PostToolUse Hook

Verifies that Write/Edit operations actually create claimed files on disk.

Purpose: Prevent false completion claims where agents mark files as "written"
but the files don't actually exist on disk.

Architecture:
- Extends PostToolUseHook base class
- Triggers on Write and Edit tools only
- Checks file existence after operation completes
- Injects warning if claimed file not created
"""

from pathlib import Path
from typing import Any

from .base import PostToolUseHook


class ImplementationVerifier(PostToolUseHook):
    """
    Verifies Write/Edit tools actually create claimed files.

    When a Write or Edit tool completes, this hook checks that the claimed
    file_path actually exists on disk. If not, it injects a warning into
    the response context.

    Environment Variables:
        IMPLEMENTATION_VERIFIER_ENABLED: "true" (default) or "false" to disable

    Configuration:
        env_var: "IMPLEMENTATION_VERIFIER_ENABLED"
        default_enabled: True
        tool_matcher: {"Write", "Edit"} - Only verifies write operations
    """

    env_var = "IMPLEMENTATION_VERIFIER_ENABLED"
    default_enabled = True
    tool_matcher = {"Write", "Edit"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Verify that the claimed file actually exists on disk.

        Args:
            tool_name: "Write" or "Edit"
            tool_input: Tool input dict with file_path or filePath key
            tool_response: Tool response dict (unused but required by interface)

        Returns:
            dict with:
                - passed: bool - True if file exists or no file to check
                - injection: str | None - Warning message if file doesn't exist
                - metadata: dict - Additional diagnostic info

        Example:
            # File exists - passes verification
            >>> hook.process("Write", {"file_path": "exists.txt"}, {})
            {"passed": True, "metadata": {"file_path": "exists.txt", "verified": True}}

            # File missing - blocks with injection
            >>> hook.process("Write", {"file_path": "missing.txt"}, {})
            {
                "passed": False,
                "injection": "⚠️ FILE NOT CREATED: missing.txt\\nYou claimed to write...",
                "metadata": {"file_path": "missing.txt", "verified": False}
            }

            # No file_path - skips verification
            >>> hook.process("Write", {}, {})
            {"passed": True, "metadata": {"reason": "no_file_path"}}
        """
        # Extract file path from tool_input (accept both snake_case and camelCase)
        file_path = tool_input.get("file_path") or tool_input.get("filePath")

        # No file path to verify - skip gracefully
        if not file_path:
            return {
                "passed": True,
                "metadata": {"reason": "no_file_path", "tool": tool_name}
            }

        # Resolve path (handle both absolute and relative paths)
        path = Path(file_path)

        # Verify file exists on disk
        if path.exists():
            return {
                "passed": True,
                "metadata": {
                    "file_path": str(path),
                    "verified": True,
                    "exists": True,
                    "tool": tool_name
                }
            }

        # File does not exist - block with warning injection
        return {
            "passed": False,
            "injection": (
                f"⚠️ FILE NOT CREATED: {file_path}\n"
                f"You claimed to write or edit this file, but it does not exist on disk. "
                f"Create it or fix the path, then rerun verification."
            ),
            "metadata": {
                "file_path": str(path),
                "verified": False,
                "exists": False,
                "tool": tool_name
            }
        }
