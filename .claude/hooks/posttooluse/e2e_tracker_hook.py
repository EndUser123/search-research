#!/usr/bin/env python3
"""E2E Tracker Hook - PostToolUse integration."""

from __future__ import annotations

import logging

# Import the standalone E2E tracker functions
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path to import PostToolUse_e2e_tracker
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from posttooluse.base import PostToolUseHook
from PostToolUse_e2e_tracker import post_tool_use_hook

# Configure logger - no stderr output
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


class E2ETrackerHook(PostToolUseHook):
    """
    PostToolUse hook for tracking end-to-end workflow execution.

    Tracks skill invocations, multi-step workflows, and tool chains
    with session isolation and security validation.

    Environment Variables:
        E2E_TRACKER_ENABLED: Enable/disable tracking (default: true)

    Security Features:
        - session_id validation (SEC-001)
        - Field validation before write (SEC-002)
        - Session isolation (session_id + terminal_id)

    Performance Features:
        - Rolling log rotation (max 1000 records)
        - Session TTL cleanup (2 hours)
    """

    env_var = "E2E_TRACKER_ENABLED"
    default_enabled = True
    # Track all tools by default
    tool_matcher = None

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Process tool event and track workflow execution.

        Args:
            tool_name: Name of tool that was used
            tool_input: Input parameters passed to tool
            tool_response: Output returned by tool

        Returns:
            Dict with results (always non-blocking)
        """
        # Extract context from tool_response
        context = tool_response.get("context", {})

        # Ensure session_id and terminal_id are present
        if "session_id" not in context:
            context["session_id"] = "unknown"
        if "terminal_id" not in context:
            context["terminal_id"] = "unknown"

        try:
            # Call the standalone E2E tracker function
            post_tool_use_hook(
                tool_name=tool_name,
                tool_input=tool_input,
                tool_output=tool_response,
                context=context
            )
        except (OSError, ValueError) as e:
            # Don't fail the tool use if tracking fails
            # Log error details without using stderr
            logger.error(f"[E2ETrackerHook] tracking error: {e}", exc_info=False)

        # Always return success (non-blocking hook)
        return {
            "passed": True,
            "tracked": True,
            "workflow_type": self._detect_workflow_type(tool_name, tool_input)
        }

    def _detect_workflow_type(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Detect workflow type from tool usage."""
        if tool_name == "Skill":
            return "skill_invocation"
        elif tool_name in ["Read", "Edit", "Write", "Bash"]:
            return "tool_chain"
        return "unknown"
