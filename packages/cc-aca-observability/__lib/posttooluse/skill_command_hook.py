#!/usr/bin/env python3
"""
SkillCommandHook - Runs skill CLI commands from SKILL.md hook declarations.

Wraps discovered hook commands (e.g., `python -m rca.hook_launcher`) as
in-process PostToolUse hooks, eliminating subprocess overhead.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from typing import Any

from posttooluse.base import PostToolUseHook

logger = logging.getLogger(__name__)


class SkillCommandHook(PostToolUseHook):
    """
    PostToolUse hook that runs skill CLI commands.

    Discovered from SKILL.md frontmatter hooks: declarations.
    Converts CLI commands to in-process execution.
    """

    def __init__(
        self,
        skill: str,
        name: str,
        command: str,
        timeout: int = 10,
        matcher_pattern: str | None = None,
    ):
        """
        Initialize SkillCommandHook.

        Args:
            skill: Skill name (e.g., "rca")
            name: Unique hook name (e.g., "rca_PostToolUse_0")
            command: CLI command to execute
            timeout: Command timeout in seconds
            matcher_pattern: Regex pattern to match tool names (None = all tools)
        """
        self.skill = skill
        self.name = name
        self.command = command
        self.timeout = timeout
        self.matcher_pattern = matcher_pattern
        # tool_matcher is None = all tools (base class default)
        # We override matches_tool() to use our regex pattern
        super().__init__()

    def matches_tool(self, tool_name: str) -> bool:
        """Check if this hook should run for the given tool."""
        if self.matcher_pattern is None:
            return True
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(re.search, self.matcher_pattern, tool_name)
                result = future.result(timeout=2)
            return result is not None
        except FuturesTimeoutError:
            logger.warning(
                f"SkillCommandHook [{self.name}] regex timed out on pattern: {self.matcher_pattern}"
            )
            return False
        except Exception:
            # Invalid regex pattern - fail safe, don't run hook
            logger.warning(
                f"SkillCommandHook [{self.name}] invalid regex pattern: {self.matcher_pattern}"
            )
            return False

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute the skill CLI command.

        Args:
            tool_name: Name of the tool that was used
            tool_input: Input parameters passed to the tool
            tool_response: Output returned by the tool

        Returns:
            Dict with execution result (empty on success, warning on failure)
        """
        if not self.enabled:
            return {}

        try:
            # Use shell=True so heredoc commands (python - <<'PY') work on Windows
            cmd = os.path.expandvars(self.command)
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                logger.warning(
                    f"SkillCommandHook [{self.name}] failed: "
                    f"exit={result.returncode}, stderr={result.stderr[:200]}"
                )
                return {
                    "warning": (
                        f"Skill hook {self.name} failed (exit {result.returncode}): "
                        f"{result.stderr[:100]}"
                    )
                }
            return {}

        except subprocess.TimeoutExpired:
            logger.warning(f"SkillCommandHook [{self.name}] timed out after {self.timeout}s")
            return {"warning": f"Skill hook {self.name} timed out after {self.timeout}s"}

        except Exception as e:
            logger.warning(f"SkillCommandHook [{self.name}] exception: {e}")
            return {"warning": f"Skill hook {self.name} error: {str(e)[:100]}"}
