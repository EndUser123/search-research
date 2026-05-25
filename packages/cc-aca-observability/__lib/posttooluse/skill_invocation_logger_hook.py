#!/usr/bin/env python3
"""
Skill Invocation Logger Hook

Logs every Skill() tool invocation to a JSONL file for easy verification.
This makes "Did Skill run?" a cheap, reliable query instead of a multi-step investigation.

Also writes to quality_log.jsonl for code quality skills to track when they were last run.

GLM5 Analysis Recommendation: "Add a tiny PostToolUse hook that logs every Skill()
invocation to a simple, human-readable log or state file (command, arguments, timestamp,
calling hook chain ID)."

Log Format (JSONL):
{
  "timestamp": "2026-03-11T15:30:45.123456",
  "skill_name": "debugRCA",
  "arguments": {"skill": "debugRCA"},
  "session_id": "console_abc123",
  "terminal_id": "terminal_def456",
  "hook_chain_id": "PostToolUse_router"
}
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import PostToolUseHook

# Add hooks lib to path for quality_log import
_hooks_lib = Path(__file__).parent.parent / "__lib"
if str(_hooks_lib) not in sys.path:
    sys.path.insert(0, str(_hooks_lib))

# Import quality log module
from quality_log import CODE_QUALITY_SKILLS, log_quality_skill

# Configure logger (no stderr output per hook best practices)
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())


class SkillInvocationLoggerHook(PostToolUseHook):
    """
    Log Skill() tool invocations to JSONL file for verification.

    Environment Variables:
        SKILL_INVOCATION_LOG_ENABLED: Enable/disable logging (default: true)
        SKILL_INVOCATION_LOG_PATH: Path to log file (default: P:/.claude/state/skill_invocations.jsonl)
    """

    env_var: str | None = "SKILL_INVOCATION_LOG_ENABLED"
    default_enabled: bool = True
    tool_matcher: set[str] = {"Skill"}  # Only log Skill tool invocations

    def __init__(self):
        super().__init__()
        self.log_path = Path(
            os.environ.get("SKILL_INVOCATION_LOG_PATH", "P:/.claude/state/skill_invocations.jsonl")
        )
        self._ensure_log_directory()

    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists."""
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"[SkillInvocationLogger] Failed to create log directory: {e}")

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Log Skill invocation to JSONL file.

        Args:
            tool_name: Should always be "Skill"
            tool_input: Tool input parameters (contains 'skill' and 'arguments')
            tool_response: Tool output (ignored for logging)

        Returns:
            {"passed": True} (non-blocking)
        """
        # Extract skill information
        skill_name = tool_input.get("skill", "unknown")
        arguments = tool_input.get("arguments", {})

        # Get session context
        session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")
        terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "unknown")

        # Create log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "skill_name": skill_name,
            "arguments": arguments,
            "session_id": session_id,
            "terminal_id": terminal_id,
            "hook_chain_id": "PostToolUse",  # This hook runs in PostToolUse
        }

        # Write to log file (JSONL format - one JSON object per line)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"[SkillInvocationLogger] Failed to write log entry: {e}")

        # Write to quality log if this is a code quality skill
        if skill_name in CODE_QUALITY_SKILLS:
            # Determine result based on tool_response
            # For skills, we consider "invoked" as a successful run
            result = "invoked"
            tier = "skill"

            # Get project root from current working directory
            project_root = Path.cwd()

            # Log to quality log
            try:
                log_quality_skill(
                    skill_name=skill_name, result=result, tier=tier, project_root=project_root
                )
            except Exception as e:
                logger.error(f"[SkillInvocationLogger] Failed to write quality log entry: {e}")

        # Non-blocking: always return passed
        return {"passed": True, "logged": True, "log_entry": log_entry}


# Hook instance for router
_hook_instance = SkillInvocationLoggerHook()


def process_prompt(data: dict) -> dict:
    """
    Router-compatible entry point.

    Args:
        data: Hook input data from PostToolUse router

    Returns:
        {"passed": True} (non-blocking)
    """
    return _hook_instance.run(data)
