#!/usr/bin/env python3
"""
Breadcrumb Tracker Hook for PostToolUse
========================================

Automatically tracks workflow steps by inferring them from tool usage.

This hook wraps the implementation from the skill-guard package.

Configuration:
- BREADCRUMB_AUTO_TRACKING_ENABLED (default: true) - Enable/disable auto-tracking
- BREADCRUMB_AUTO_TRACKING_MODE (default: advisory) - warn or block modes

Author: Skill Enforcement v2.0
Date: 2026-03-10
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Add skill-guard to path
# Original location was P:/packages/skill-guard/src; plugin moved to
# P:/packages/.claude-marketplace/plugins/skill-guard/src during the
# marketplace consolidation. Check both so the hook works regardless of
# which layout is present.
for _candidate in (
    Path("P:/packages/.claude-marketplace/plugins/skill-guard/src"),
    Path("P:/packages/skill-guard/src"),  # legacy location
):
    if _candidate.exists():
        sys.path.insert(0, str(_candidate))
        break

# Import posttooluse base class
from posttooluse.base import PostToolUseHook

# Import the actual breadcrumb tracking logic
from skill_guard.breadcrumb.hooks.PostToolUse_breadcrumb_tracker import (
    run as breadcrumb_tracker_run,
)


class BreadcrumbTrackerHook(PostToolUseHook):
    """Automatic breadcrumb tracking via tool pattern inference."""

    def __init__(self):
        """Initialize breadcrumb tracker hook."""
        super().__init__()
        # Import configuration
        import os
        self.enabled = os.environ.get("BREADCRUMB_AUTO_TRACKING_ENABLED", "true").lower() == "true"
        self.mode = os.environ.get("BREADCRUMB_AUTO_TRACKING_MODE", "advisory")

    @property
    def tool_matcher(self) -> str | None:
        """Match all tools - breadcrumb tracking applies to all tool usage."""
        return "*"  # Track all tools

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """Process the tool result for breadcrumb tracking.

        Args:
            tool_name: Name of the tool that was used
            tool_input: Input parameters passed to the tool
            tool_response: Output returned by the tool

        Returns:
            Dict with results from breadcrumb tracking
        """
        if not self.enabled:
            return {"passed": True, "skipped": True}

        # Reconstruct data dict expected by breadcrumb_tracker_run
        data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_response": tool_response,
        }

        # Delegate to actual breadcrumb tracker implementation
        result = breadcrumb_tracker_run(data)
        if result:
            result.setdefault("passed", True)
            return result
        # Always return a dict (breadcrumb_tracker_run might return None for no-op cases)
        return {"passed": True, "skipped": True}

