#!/usr/bin/env python3
"""
Workflow Completion Tracker
===========================

PostToolUse hook that tracks workflow completion criteria satisfaction.

Monitors tool outputs for WORKFLOW:{skill}:{action} markers and updates
the skill execution state accordingly.

Phase transitions:
- Skill() called -> phase=loaded
- First workflow tool -> phase=executing
- All completion_criteria satisfied -> phase=complete
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Add parent hooks directory for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class WorkflowCompletionTracker(PostToolUseHook):
    """Track workflow completion criteria via output markers."""

    # Track on all tools - we need to check outputs for completion markers
    tool_matcher = None  # Match all tools
    env_var = "WORKFLOW_COMPLETION_TRACKER_ENABLED"
    default_enabled = True

    def __init__(self):
        super().__init__()
        self._import_functions()

    def _import_functions(self):
        """Lazy import state management functions."""
        try:
            from skill_execution_state import (
                mark_first_tool_validated,
                read_pending_state,
                transition_phase,
            )

            self._read_pending_state = read_pending_state
            self._transition_phase = transition_phase
            self._mark_first_tool_validated = mark_first_tool_validated
            self._imports_ok = True
        except ImportError:
            self._read_pending_state = lambda: None
            self._transition_phase = lambda _s: False
            self._mark_first_tool_validated = lambda: None
            self._imports_ok = False

    def process(
        self, tool_name: str, _tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Track workflow completion based on tool outputs.

        Non-blocking - just tracks state for the Stop hook to validate.
        """
        if not self._imports_ok:
            return {"passed": True, "skipped": True, "reason": "import_failed"}

        state = self._read_pending_state()
        if state is None:
            return {"passed": True, "skipped": True, "reason": "no_pending_skill"}

        skill_name = state.get("skill", "")
        current_phase = state.get("phase", "pending")

        # Extract tool output text for marker matching
        output_text = self._extract_output_text(tool_response)

        # Check for completion criteria satisfaction
        if skill_name and output_text:
            self._check_completion_markers(state, output_text)

        # Phase transitions based on tool usage
        if tool_name == "Skill":
            # Skill tool called -> transition to loaded
            self._transition_phase("loaded")
            return {"passed": True, "metadata": {"phase_transition": "loaded"}}

        # First workflow tool after skill load -> transition to executing
        if current_phase == "loaded" and tool_name in self._get_workflow_tools():
            self._transition_phase("executing")

            # Also mark first tool as validated (for first-tool coherence tracking)
            self._mark_first_tool_validated()

            return {"passed": True, "metadata": {"phase_transition": "executing"}}

        return {"passed": True}

    def _extract_output_text(self, tool_response: dict[str, Any]) -> str:
        """Extract text content from tool response for marker matching."""
        if isinstance(tool_response, dict):
            # Common output fields
            for field in ("output", "text", "content", "result", "stdout", "response"):
                if field in tool_response:
                    value = tool_response[field]
                    if isinstance(value, str):
                        return value
                    elif isinstance(value, dict) and "text" in value:
                        return str(value["text"])
                    elif isinstance(value, dict) and "content" in value:
                        return str(value["content"])

            # Handle nested structures
            if "tool_result" in tool_response:
                return self._extract_output_text(tool_response["tool_result"])

        elif isinstance(tool_response, str):
            return tool_response

        return ""

    def _get_workflow_tools(self) -> set[str]:
        """Get set of tools that count as workflow execution."""
        return {"Bash", "Read", "Grep", "Glob", "Write", "Edit", "Task", "Agent"}

    def _check_completion_markers(self, state: dict[str, Any], output_text: str) -> None:
        """
        Check if tool output contains WORKFLOW markers that satisfy completion criteria.

        Args:
            state: Current skill execution state
            output_text: Text from tool output to check
        """
        skill_name = state.get("skill", "")
        if not skill_name:
            return

        completion_criteria = state.get("completion_criteria", [])
        if not completion_criteria:
            return

        # Build regex pattern for this skill's markers
        # Pattern: WORKFLOW:{skill}:{action}
        marker_pattern = re.compile(rf"WORKFLOW:{re.escape(skill_name)}:(\w+)", re.IGNORECASE)

        # Find all markers in output
        found_markers = set(marker_pattern.findall(output_text))
        if not found_markers:
            return

        # Check each criterion for satisfaction
        any_satisfied = False
        for criterion in completion_criteria:
            if isinstance(criterion, dict):
                required_output = criterion.get("required_output", "")
                # Extract action from required_output (format: WORKFLOW:{skill}:{action})
                action_match = re.search(r"WORKFLOW:\w+:(\w+)", required_output, re.IGNORECASE)
                if action_match:
                    action = action_match.group(1).lower()
                    if action in found_markers:
                        # Mark as satisfied (would update state here if we had a write function)
                        any_satisfied = True

        # If all criteria satisfied, transition to complete
        if any_satisfied:
            # Check if all criteria are now satisfied
            all_satisfied = self._all_criteria_satisfied(state, found_markers)
            if all_satisfied:
                self._transition_phase("complete")

    def _all_criteria_satisfied(self, state: dict[str, Any], found_markers: set[str]) -> bool:
        """Check if all completion criteria have been satisfied."""
        completion_criteria = state.get("completion_criteria", [])
        if not completion_criteria:
            return False

        marker_pattern = re.compile(
            rf"WORKFLOW:{re.escape(state.get('skill', ''))}:(\w+)", re.IGNORECASE
        )

        for criterion in completion_criteria:
            if isinstance(criterion, dict):
                required_output = criterion.get("required_output", "")
                action_match = marker_pattern.search(required_output)
                if action_match:
                    action = action_match.group(1).lower()
                    if action not in found_markers:
                        return False

        return True
