#!/usr/bin/env python3
"""
Characterization Capture Hook

Captures AST characterization of hook files after Edit/Write operations.
Stores to .state/characterization/ for session-start drift comparison.

Passive: captures on hook edits, never blocks.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Configure logger - no stderr (Claude Code treats stderr as hook error)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

_char_engine_ok = False
try:
    from characterization_engine import CharacterizationEngine
    _char_engine_ok = True
except ImportError:
    CharacterizationEngine = None

_state_mgr_ok = False
try:
    from protection_state import StateManager
    _state_mgr_ok = True
except ImportError:
    StateManager = None


class CharacterizationCaptureHook:
    """PostToolUse hook that captures characterization after hook edits."""

    env_var = "CHARACTERIZATION_CAPTURE_ENABLED"
    default_enabled = True
    # Only trigger on Edit/Write targeting hook files
    tool_matcher = {"Edit", "Write"}

    def __init__(self):
        self.enabled = os.environ.get(self.env_var, "true").lower() not in ("false", "0", "no")

    def process(self, data: dict) -> dict | None:
        """Capture characterization after hook file edits.

        Args:
            data: PostToolUse event data with tool_name, tool_input, tool_result

        Returns:
            None (passive hook - no blocking output)
        """
        if not self.enabled:
            return None

        # Accept both tool_input and toolInput variants
        tool_input = data.get("tool_input") or data.get("toolInput") or {}
        tool_name = data.get("tool_name", "")

        # Validate tool_matcher - only run on Edit/Write
        if tool_name not in self.tool_matcher:
            return None

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return None

        # Only process hook files
        if not self._is_hook_file(file_path):
            return None

        try:
            if not _char_engine_ok or CharacterizationEngine is None:
                return None
            char_data = engine.capture_characterization(str(file_path))
            if char_data is None:
                return None

            if _state_mgr_ok and StateManager is not None:
                state_mgr = StateManager()
                state_mgr.save_characterization(char_data)
                logger.debug(f"Captured characterization: {file_path}")

        except Exception as e:
            # Fail silently - capture errors should not block tool response
            logger.debug(f"Characterization capture failed for {file_path}: {e}")

        return None

    def _is_hook_file(self, file_path: str) -> bool:
        """Check if file is in the hooks directory (not a sibling like hooks_archive)."""
        try:
            hooks_dir = HOOKS_DIR.resolve()
            file_resolved = Path(file_path).resolve()
            # Use is_relative_to (Python 3.9+) or check with separator to avoid
            # P:/.claude/hooks triggering on P:/.claude/hooks_archive
            if hasattr(file_resolved, 'is_relative_to'):
                return file_resolved.is_relative_to(hooks_dir)
            else:
                hooks_str = str(hooks_dir) + os.sep
                return str(file_resolved).startswith(hooks_str)
        except Exception:
            return False
